#!/usr/bin/env bash
# This runs the worker on periodic burst mode so that changes made to tasks
# during development will be applied when the worker executes them
while true; do
    python /app/manage.py rqworker --burst default cavatica dataservice aws slack releases ingest
    sleep 10
done
