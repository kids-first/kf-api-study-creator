#!/bin/bash
set -e
set +x
if [[ "$WORKER" == "true" ]]; then
    echo "Starting worker"
    supervisord -c  /etc/supervisor/conf.d/worker.conf
elif [[ "$1" == "scheduler" ]]; then
    echo "Starting scheduler"
    /app/manage.py schedule_jobs
    supervisord -c  /etc/supervisor/conf.d/scheduler.conf
else
    echo "Starting service"
    echo "Migrate"
    /app/manage.py migrate
    echo "Setup Permissions"
    /app/manage.py setup_permissions
    echo "Execute Gunicorn"
    exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
fi
