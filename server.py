import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from datetime import datetime
from flask import Flask, request, Response, send_file, abort

app = Flask(__name__)

JAVAC = "javac"
JAVA = "java"

PUBLIC_DIR = "/app/public"
TESTERS_DIR = "/app/testers"

PUBLIC_ALLOWLIST = {
    "handout.md": ("text/markdown", True),
    "exam.seb": ("application/octet-stream", True),
    "Store.java": ("text/plain", True),
    "StoreConsole.class": ("application/octet-stream", True),
}

WORK_ROOT = "/work"
DATA_ROOT = "/data"  # must be a writable volume mount

COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 6

MAX_FILES = 80
MAX_TOTAL_BYTES = 4_000_000

ALLOWED_EXT = {".java", ".class", ".zip"}

# Public flags only; testers remain private
TESTER_BY_FLAG = {
    "-p1": "ExceptionTesters",
    "-p2": "ProductTester",
    "-p3": "OrderTester",
    "-p4": "StoreTester",
}
STRIP_SELECTION_FLAGS = True

# Max tries per (ip, -pX)
MAX_TRIES_PER_IP_PER_PROJECT = 3

# Student number sanity (adjust to your format)
STUDENT_RE = re.compile(r"^[0-9A-Za-z_-]{3,32}$")

DB_PATH = os.path.join(DATA_ROOT, "attempts.sqlite3")

def ensure_db():
    os.makedirs(DATA_ROOT, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                ip TEXT NOT NULL,
                project TEXT NOT NULL,
                count INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (ip, project)
            )
        """)
        conn.commit()

def get_client_ip():
    # If you later put a reverse proxy, you can prefer X-Forwarded-For safely there.
    return request.remote_addr or "unknown"

def increment_and_check_attempt(ip: str, project: str) -> int:
    """
    Increments attempt counter for (ip, project).
    Returns new count after increment.
    """
    ensure_db()
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT count FROM attempts WHERE ip=? AND project=?",
            (ip, project),
        ).fetchone()

        if row is None:
            new_count = 1
            conn.execute(
                "INSERT INTO attempts(ip, project, count, updated_at) VALUES(?,?,?,?)",
                (ip, project, new_count, now),
            )
        else:
            new_count = int(row[0]) + 1
            conn.execute(
                "UPDATE attempts SET count=?, updated_at=? WHERE ip=? AND project=?",
                (new_count, now, ip, project),
            )

        conn.commit()
    return new_count

def run(cmd, cwd, timeout):
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            text=True,
        )
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or "") + "\n[TIMEOUT]\n"

def safe_name(name: str) -> str:
    return os.path.basename(name.replace("\\", "/"))

def choose_project_and_args(args_str: str):
    try:
        args = shlex.split(args_str or "")
    except ValueError as e:
        raise ValueError(f"Bad args string: {e}")

    found = [a for a in args if a in TESTER_BY_FLAG]
    if len(found) == 0:
        allowed = " ".join(sorted(TESTER_BY_FLAG.keys()))
        raise ValueError(f"No project flag provided. Use one of: {allowed}")
    if len(found) > 1:
        raise ValueError(f"Multiple project flags provided: {', '.join(found)} (choose exactly one)")

    project_flag = found[0]
    tester = TESTER_BY_FLAG[project_flag]

    if STRIP_SELECTION_FLAGS:
        args = [a for a in args if a not in TESTER_BY_FLAG]

    return project_flag, tester, args

def collect_uploads_to(workdir: str):
    saved = []
    total = 0

    if "files" in request.files:
        files = request.files.getlist("files")
    elif "file" in request.files:
        files = [request.files["file"]]
    else:
        return [], "Missing multipart field 'files' (multi) or 'file' (single).\n"

    if len(files) > MAX_FILES:
        return [], f"Too many files (max {MAX_FILES}).\n"

    for f in files:
        fname = safe_name(f.filename or "")
        if not fname:
            return [], "One upload has an empty filename.\n"

        _, ext = os.path.splitext(fname)
        ext = ext.lower()
        if ext not in ALLOWED_EXT:
            return [], f"Disallowed extension: {fname}\n"

        dst = os.path.join(workdir, fname)
        f.save(dst)
        size = os.path.getsize(dst)
        total += size
        if total > MAX_TOTAL_BYTES:
            return [], "Upload too large.\n"
        saved.append(dst)

    return saved, None

def unzip_into_flat(workdir: str, zippath: str):
    extracted = []
    with zipfile.ZipFile(zippath, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = safe_name(info.filename)
            _, ext = os.path.splitext(name)
            ext = ext.lower()
            if ext not in {".java", ".class"}:
                continue
            if len(extracted) >= MAX_FILES:
                break
            outpath = os.path.join(workdir, name)
            with z.open(info) as src, open(outpath, "wb") as dst:
                data = src.read()
                if len(data) > MAX_TOTAL_BYTES:
                    continue
                dst.write(data)
            extracted.append(outpath)
    return extracted

@app.get("/")
def health():
    return "OK\n"

@app.get("/public/<path:name>")
def download_public(name):
    if name not in PUBLIC_ALLOWLIST:
        abort(404)

    mime, as_attachment = PUBLIC_ALLOWLIST[name]
    path = os.path.join(PUBLIC_DIR, name)

    if not os.path.isfile(path):
        abort(404)

    return send_file(
        path,
        mimetype=mime,
        as_attachment=as_attachment,
        download_name=name,
        conditional=True,
        max_age=3600,   # optional cache
    )

@app.get("/public")
def list_public():
    # Return a simple text list of allowed files
    lines = ["Available downloads:"]
    for k in sorted(PUBLIC_ALLOWLIST.keys()):
        lines.append(f"- /public/{k}")
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.post("/submit")
def submit():
    args_str = (request.form.get("args") or "").strip()
    try:
        project_flag, tester, tester_args = choose_project_and_args(args_str)
    except ValueError as e:
        return Response(str(e) + "\n", status=400, mimetype="text/plain")

    ip = get_client_ip()
    attempt = increment_and_check_attempt(ip, project_flag)
    if attempt > MAX_TRIES_PER_IP_PER_PROJECT:
        return Response(
            f"Too many attempts for {project_flag} from your IP ({ip}). Max is {MAX_TRIES_PER_IP_PER_PROJECT}.\n",
            status=429,
            mimetype="text/plain",
        )

    workdir = tempfile.mkdtemp(prefix="job_", dir=WORK_ROOT)
    try:
        saved, err = collect_uploads_to(workdir)
        if err:
            return Response(err, status=400, mimetype="text/plain")

        expanded = []
        for p in list(saved):
            if p.lower().endswith(".zip"):
                expanded.extend(unzip_into_flat(workdir, p))
        if expanded:
            for p in saved:
                if p.lower().endswith(".zip"):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            saved = [p for p in saved if not p.lower().endswith(".zip")] + expanded

        java_files = [os.path.basename(p) for p in saved if p.lower().endswith(".java")]
        class_files = [os.path.basename(p) for p in saved if p.lower().endswith(".class")]

        if not java_files and not class_files:
            return Response("No .java or .class files found.\n", status=400, mimetype="text/plain")

        if java_files:
            rc, out = run(
                [JAVAC, "-cp", TESTERS_DIR, "-d", workdir] + java_files,
                cwd=workdir,
                timeout=COMPILE_TIMEOUT,
            )
            if rc != 0:
                return Response("=== COMPILE ERROR ===\n" + out, status=200, mimetype="text/plain")

        cmd = [JAVA, "-Xmx256m", "-cp", f"{TESTERS_DIR}:{workdir}", tester] + tester_args
        rc, out = run(cmd, cwd=workdir, timeout=RUN_TIMEOUT)

        return Response(out + f"\n[exit_code={rc}]\n", status=200, mimetype="text/plain")

    finally:
        shutil.rmtree(workdir, ignore_errors=True)

@app.post("/submit-all")
def submit_all():
    """
    Accepts:
      - student: student number (required)
      - files=... or file=... (same rules as /submit)
    Saves permanently to /data/submissions/<student>/<timestamp>_<suffix>/
    Responds with env-provided message (no tester names revealed).
    """
    student = (request.form.get("student") or "").strip()
    if not STUDENT_RE.match(student):
        return Response("Invalid or missing 'student' field.\n", status=400, mimetype="text/plain")

    # Permanent directory
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = next(tempfile._get_candidate_names())
    dest_dir = os.path.join(DATA_ROOT, "submissions", student, f"{ts}_{suffix}")
    os.makedirs(dest_dir, exist_ok=True)

    # Save into a temp dir first, then move into dest_dir (atomic-ish)
    tmpdir = tempfile.mkdtemp(prefix="collect_", dir=WORK_ROOT)
    try:
        saved, err = collect_uploads_to(tmpdir)
        if err:
            return Response(err, status=400, mimetype="text/plain")

        expanded = []
        for p in list(saved):
            if p.lower().endswith(".zip"):
                expanded.extend(unzip_into_flat(tmpdir, p))
        if expanded:
            for p in saved:
                if p.lower().endswith(".zip"):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            saved = [p for p in saved if not p.lower().endswith(".zip")] + expanded

        kept = 0
        for p in saved:
            name = os.path.basename(p)
            shutil.move(p, os.path.join(dest_dir, name))
            kept += 1

        # Reply message comes from env-file variable
        template = os.environ.get("SUBMIT_ALL_MESSAGE", "Submission received.")
        # Optional simple templating
        msg = template.format(student=student, files=kept, folder=os.path.basename(dest_dir))
        return Response(msg + "\n", status=200, mimetype="text/plain")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
