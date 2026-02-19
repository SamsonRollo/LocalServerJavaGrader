FROM eclipse-temurin:25-jdk-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip tini unzip \
 && pip3 install --no-cache-dir flask waitress \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10001 grader

WORKDIR /app
COPY testers /app/testers
COPY public /app/public
COPY server.py /app/server.py

# Compile testers ONCE
RUN find /app/testers -name "*.java" -print0 | xargs -0 javac

RUN chown -R grader:grader /app
USER grader

EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini","--"]

# Use waitress for concurrent student submissions
ENV TMPDIR=/tmp
CMD ["python3","-c","from waitress import serve; import server; serve(server.app, host='0.0.0.0', port=8080, threads=16)"]

