import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
import markdown
from datetime import datetime
from flask import Flask, request, Response, send_file, abort
from markupsafe import escape


app = Flask(__name__)

TOKEN_RE = re.compile(r"^[A-Za-z0-9 _-]{1,64}$")
JAVAC = "javac"
JAVA = "java"

PUBLIC_DIR = "/app/public"
TESTERS_DIR = "/app/testers"

PUBLIC_ALLOWLIST = {
    "handout.md": ("text/markdown", True),
    "sample.md": ("text/markdown", False),
    "exam.seb": ("application/octet-stream", True),
    "gl.seb": ("application/octet-stream", True),

    # SQL file
    "education.sql": ("application/sql", False),

    # source files
    "Library.java": ("text/plain", False),
    
    # compiled console runner
    "LibraryConsole.class": ("application/octet-stream", False),
    "BankingPaymentTester.class": ("application/octet-stream", True),

    # optional scripts for students
    "submit-m1.ps1": ("text/plain", False),
    "submit-m2.ps1": ("text/plain", False),
    "submit-m3.ps1": ("text/plain", False),
    "submit-m4.ps1": ("text/plain", False),
    "submit-all.ps1": ("text/plain", False),
    "clean-workspace.ps1": ("text/plain", True),
    "FUChecker.ps1": ("text/plain", False),
    "GLChecker.ps1": ("text/plain", True),
}
WORK_ROOT = "/work"
DATA_ROOT = "/data"  # must be a writable volume mount

COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 6

MAX_FILES = 80
MAX_TOTAL_BYTES = 4_000_000

ALLOWED_EXT = {".java", ".class", ".zip", ".md"}

# Public flags only; testers remain private
TESTER_BY_FLAG = {
    # "-m1": "LibraryExceptionTester",
    # "-m2": "BookTester",
    # "-m3": "BorrowRecordTester",
    # "-m4": "LibraryTester",
    "-FUL": "SomeClassTester",
}
STRIP_SELECTION_FLAGS = True

# Max tries per (indentity, -pX)
MAX_TRIES_PER_IP_PER_PROJECT = 1

# Student number sanity (adjust to your format)
STUDENT_RE = re.compile(r"^[0-9A-Za-z_-]{3,32}$")

DB_PATH = os.path.join(DATA_ROOT, "attempts.sqlite3")

def ensure_db():
    os.makedirs(DATA_ROOT, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                indentity TEXT NOT NULL,
                project TEXT NOT NULL,
                count INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (indentity, project)
            )
        """)
        conn.commit()

def get_client_ip():
    # If you later put a reverse proxy, you can prefer X-Forwarded-For safely there.
    return request.remote_addr or "unknown"

def increment_and_check_attempt(indentity: str, project: str) -> int:
    """
    Increments attempt counter for (indentity, project).
    Returns new count after increment.
    """
    ensure_db()
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT count FROM attempts WHERE indentity=? AND project=?",
            (indentity, project),
        ).fetchone()

        if row is None:
            new_count = 1
            conn.execute(
                "INSERT INTO attempts(indentity, project, count, updated_at) VALUES(?,?,?,?)",
                (indentity, project, new_count, now),
            )
        else:
            new_count = int(row[0]) + 1
            conn.execute(
                "UPDATE attempts SET count=?, updated_at=? WHERE indentity=? AND project=?",
                (new_count, now, indentity, project),
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


def get_identity():
    # token from submit script: curl.exe -F "t=TOKEN"
    t = (request.form.get("t") or request.args.get("t") or "").strip()
    if t and TOKEN_RE.fullmatch(t):
        return t
    return request.remote_addr or "unknown"


@app.post("/submit")
def submit():
    args_str = (request.form.get("args") or "").strip()
    try:
        project_flag, tester, tester_args = choose_project_and_args(args_str)
    except ValueError as e:
        return Response(str(e) + "\n", status=400, mimetype="text/plain")

    indentity = get_identity()
    attempt = increment_and_check_attempt(indentity, project_flag)
    if attempt > MAX_TRIES_PER_IP_PER_PROJECT:
        return Response(
            f"Too many attempts for {project_flag} from your ID ({indentity}). Max is {MAX_TRIES_PER_IP_PER_PROJECT}.\n",
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
    student = (request.form.get("student") or "").strip()
    if not STUDENT_RE.match(student):
        return Response("Invalid or missing 'student' field.\n", status=400, mimetype="text/plain")

    args_str = (request.form.get("args") or "").strip()

    tester = None
    tester_args = []
    project_flag = None  # ### NEW

    if args_str:
        try:
            project_flag, tester, tester_args = choose_project_and_args(args_str)
        except ValueError as e:
            return Response(str(e) + "\n", status=400, mimetype="text/plain")

        # ### NEW: enforce max 1 try only when -FUL is used
        if project_flag == "-FUL":
            # Prefer per-student limiting (avoid IP collisions in labs/NAT)
            indentity = student
            attempt = increment_and_check_attempt(indentity, project_flag)
            if attempt > MAX_TRIES_PER_IP_PER_PROJECT:
                return Response(
                    f"Too many attempts for {project_flag} for student ({student}). "
                    f"Max is {MAX_TRIES_PER_IP_PER_PROJECT}.\n",
                    status=429,
                    mimetype="text/plain",
                )

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = next(tempfile._get_candidate_names())
    dest_dir = os.path.join(DATA_ROOT, "submissions", student, f"{ts}_{suffix}")
    os.makedirs(dest_dir, exist_ok=True)

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
                    os.remove(p)
            saved = [p for p in saved if not p.lower().endswith(".zip")] + expanded

        # store permanently
        for p in saved:
            shutil.move(p, os.path.join(dest_dir, os.path.basename(p)))

        tester_output = ""

        if tester:
            java_files = [f for f in os.listdir(dest_dir) if f.endswith(".java")]

            if java_files:
                rc, out = run(
                    [JAVAC, "-cp", TESTERS_DIR, "-d", dest_dir] + java_files,
                    cwd=dest_dir,
                    timeout=COMPILE_TIMEOUT,
                )

                if rc != 0:
                    return Response("=== COMPILE ERROR ===\n" + out, mimetype="text/plain")

            rc, out = run(
                [JAVA, "-cp", f"{TESTERS_DIR}:{dest_dir}", tester] + tester_args,
                cwd=dest_dir,
                timeout=RUN_TIMEOUT,
            )

            tester_output = "\n=== TEST RESULT ===\n" + out

        template = os.environ.get("SUBMIT_ALL_MESSAGE", "Submission received.")
        msg = template.format(student=student, files=len(saved), folder=os.path.basename(dest_dir))

        return Response(msg + tester_output + "\n", mimetype="text/plain")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def load_handout_md() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "handout.md")  # same level as server.py
    if not os.path.isfile(path):
        abort(404)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/handout")
def view_handout():
    md_text = load_handout_md()

    # Render markdown -> HTML with better extensions + pygments highlighting
    try:
        import markdown
        from pygments.formatters import HtmlFormatter

        # VS Code-ish highlighting: pick a Pygments style you like.
        # Options: "github-dark", "friendly", "monokai", "native", "stata-dark", etc.
        # If a style isn't available in your environment, Pygments falls back.
        pygments_style = os.environ.get("PYGMENTS_STYLE", "github-dark")
        pygments_css = HtmlFormatter(style=pygments_style).get_style_defs(".highlight")

        md = markdown.Markdown(
            extensions=[
                "extra",
                "tables",
                "toc",
                "fenced_code",
                "md_in_html",
                "attr_list",
                "def_list",
                "admonition",
                "pymdownx.superfences",
                "pymdownx.highlight",
                "pymdownx.inlinehilite",
                "pymdownx.tasklist",
                "pymdownx.emoji",
                "pymdownx.tilde",
                "pymdownx.details",
                "pymdownx.magiclink",
            ],
            extension_configs={
                "pymdownx.tasklist": {"custom_checkbox": True},
                "pymdownx.highlight": {
                    "use_pygments": True,
                    "guess_lang": False,
                    "css_class": "highlight",
                    "linenums": False,
                },
                "toc": {"permalink": True},
            },
            output_format="html5",
        )

        html_body = md.convert(md_text)

    except Exception:
        pygments_css = ""
        html_body = "<pre>" + escape(md_text) + "</pre>"

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Handout</title>

  <style>
    /* --- VS Code-ish layout --- */
    :root {{
      --fg: #24292f;
      --muted: #57606a;
      --bg: #ffffff;
      --border: rgba(27,31,36,0.15);
      --code-bg: rgba(175,184,193,0.2);
      --blockquote-bg: rgba(175,184,193,0.12);
      --link: #0969da;
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --fg: #e6edf3;
        --muted: #8b949e;
        --bg: #0d1117;
        --border: rgba(240,246,252,0.15);
        --code-bg: rgba(240,246,252,0.12);
        --blockquote-bg: rgba(240,246,252,0.08);
        --link: #2f81f7;
      }}
    }}

    html, body {{
      background: var(--bg);
      color: var(--fg);
    }}

    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      line-height: 1.6;
      max-width: 980px;
      margin: 28px auto;
      padding: 0 18px;

      /* deter casual copy */
      -webkit-user-select: none;
      user-select: none;
    }}

    /* Allow selecting code blocks and inline code */
    code,
    pre,
    pre *,
    .highlight,
    .highlight *,
    code *,
    kbd,
    samp {{
      -webkit-user-select: text !important;
      user-select: text !important;
    }}

    article {{
      font-size: 16px;
    }}

    /* Headings similar to VS Code markdown preview */
    h1, h2, h3, h4, h5, h6 {{
      margin-top: 1.2em;
      margin-bottom: 0.6em;
      font-weight: 600;
      line-height: 1.25;
    }}
    h1 {{ font-size: 2.0em; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }}
    h2 {{ font-size: 1.6em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }}
    h3 {{ font-size: 1.3em; }}
    h4 {{ font-size: 1.1em; }}

    p {{ margin: 0.6em 0; }}
    ul, ol {{ margin: 0.6em 0 0.6em 1.4em; }}
    li {{ margin: 0.2em 0; }}

    a {{
      color: var(--link);
      text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}

    hr {{
      border: 0;
      border-top: 1px solid var(--border);
      margin: 1.2em 0;
    }}

    /* Inline code */
    code {{
      background: var(--code-bg);
      padding: 0.15em 0.35em;
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 0.95em;
    }}

    /* Code blocks */
    pre {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
      overflow: auto;
      margin: 0.9em 0;
    }}
    pre code {{
      background: none;
      padding: 0;
      border-radius: 0;
      font-size: 0.92em;
      line-height: 1.5;
      display: block;
      white-space: pre;
    }}

    /* Blockquotes */
    blockquote {{
      margin: 0.9em 0;
      padding: 0.2em 1em;
      border-left: 4px solid var(--border);
      background: var(--blockquote-bg);
      border-radius: 8px;
      color: var(--muted);
    }}
    blockquote p {{ margin: 0.6em 0; }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 0.9em 0;
      overflow: hidden;
      border: 1px solid var(--border);
      border-radius: 10px;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 10px 12px;
      vertical-align: top;
    }}
    th {{
      text-align: left;
      font-weight: 600;
      background: var(--blockquote-bg);
    }}
    tr:last-child td {{ border-bottom: none; }}

    /* Images */
    img {{
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      border: 1px solid var(--border);
    }}

    /* Task lists (pymdownx.tasklist) */
    .task-list-item {{
      list-style: none;
      margin-left: -1.2em;
    }}
    .task-list-item input[type="checkbox"] {{
      margin-right: 0.6em;
      transform: translateY(1px);
    }}

    /* TOC permalink (from toc extension) */
    .toclink, .headerlink {{
      color: var(--muted);
      margin-left: 0.35em;
      text-decoration: none;
      opacity: 0.7;
      font-size: 0.9em;
    }}
    .toclink:hover, .headerlink:hover {{
      opacity: 1.0;
      text-decoration: none;
    }}

    /* Pygments syntax highlighting */
    {pygments_css}

    @media print {{
      body {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <article id="content">
    {html_body}
  </article>

  <script>
    // Deter common actions (bypassable)
    document.addEventListener("contextmenu", e => e.preventDefault());
    document.addEventListener("keydown", function(e) {{
      const k = (e.key || "").toLowerCase();
      if ((e.ctrlKey || e.metaKey) && (k === "p" || k === "s" || k === "u")) {{
        e.preventDefault();
      }}
    }});
  </script>
</body>
</html>"""

    resp = Response(html, mimetype="text/html; charset=utf-8")
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'none'; "
        "style-src 'unsafe-inline'; "
        "script-src 'unsafe-inline'; "
        "img-src data:; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'"
    )
    resp.headers["Content-Disposition"] = "inline; filename=handout.html"
    return resp