#!/bin/bash

WATCH_DIR="/home/null_trace/java-grader/data/submissions"

inotifywait -m -e create -e moved_to --format '%f' "$WATCH_DIR" | while read NEWDIR
do
    FULL="$WATCH_DIR/$NEWDIR"

    if [ -d "$FULL" ]; then
        echo "New submission: $FULL"
        tree "$FULL"
    fi
done