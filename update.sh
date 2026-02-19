#!/bin/bash
sudo docker build -t java-grader:latest .
sudo docker rm -f java-grader 2>/dev/null || true

sudo docker run -d --name java-grader \
  -p 8080:8080 \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /work:exec,size=512m \
  --tmpfs /run \
  -v java-grader-data:/data \
  --env-file .env \
  -e TMPDIR=/tmp \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --restart unless-stopped \
  java-grader:latest