#!/bin/bash
/app/manage.py migrate
pip install -r /app/dev-requirements.txt
/app/manage.py fakestudies -n 3
/app/manage.py fakefiles

# Make an admin user
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python manage.py shell
/app/manage.py runserver 0.0.0.0:8080
