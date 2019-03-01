#!/bin/bash
/app/manage.py migrate
exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
