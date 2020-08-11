#!/bin/ash
if $WORKER ; then
    supervisord -c  /etc/supervisor/conf.d/worker.conf
elif [[ $1 = scheduler ]]; then
    /app/manage.py schedule_jobs
    supervisord -c  /etc/supervisor/conf.d/scheduler.conf
else
    python manage.py syncstudies --api $DATASERVICE_URL
    /app/manage.py migrate
    /app/manage.py setup_permissions
    exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
fi
