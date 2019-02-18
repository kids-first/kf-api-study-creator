#!/bin/bash
/app/manage.py migrate
/app/manage.py loaddata studies
/app/manage.py loaddata files
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python manage.py shell
/app/manage.py runserver 0.0.0.0:8080
