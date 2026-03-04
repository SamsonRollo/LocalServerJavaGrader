#!/bin/bash
set -e

WATCH_DIR="/home/null_trace/java-grader/data/submissions"
WATCH_SCRIPT="/home/null_trace/java-grader/watch-submissions.sh"

sudo docker build -t java-grader:latest .

# kill anything binding 8081
sudo docker ps -aq --filter "publish=8081" | xargs -r sudo docker rm -f

# remove known containers
sudo docker rm -f java-grader java-grader_grader_1 80c58d41a5e2_java-grader_grader_1 2>/dev/null || true

sudo docker run -d --name java-grader \
  -p 8081:8081 \
  --read-only \
  --tmpfs /tmp:uid=10001,gid=10001,mode=1777 \
  --tmpfs /work:exec,size=512m,uid=10001,gid=10001,mode=1777 \
  --tmpfs /run:uid=10001,gid=10001,mode=755 \
  -v /home/null_trace/java-grader/data:/data \
  -v /home/null_trace/java-grader/handout.md:/app/handout.md:ro \
  --env-file .env \
  -e TMPDIR=/tmp \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --restart unless-stopped \
  java-grader:latest

# start watcher if not already running
if ! pgrep -f watch-submissions.sh >/dev/null; then
    echo "Starting submission watcher..."
    nohup "$WATCH_SCRIPT" > /home/null_trace/java-grader/watcher.log 2>&1 &
fi