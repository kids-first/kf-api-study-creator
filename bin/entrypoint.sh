#!/bin/bash
/app/manage.py migrate
exec /app/manage.py runserver 0.0.0.0:8080
