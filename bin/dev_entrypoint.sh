#!/bin/ash
#!/bin/sh
# wait-for-postgres.sh

set -e

until PGPASSWORD=$PG_PASS psql -h "$PG_HOST" -U "$PG_USER" -c '\q'; do
      >&2 echo "Postgres is unavailable - sleeping"
    sleep 2
done

>&2 echo "Postgres is up - executing command"


/app/manage.py migrate


case $PRELOAD_DATA in
    "DATASERVICE")
        echo "Will load studies from the default dataservice"
        python manage.py syncstudies
        ;;
    http*)
        echo Will load studies from $PRELOAD_DATA
        python manage.py syncstudies --api $PRELOAD_DATA
        ;;
    "FAKE")
        echo "Will create fake data"
        /app/manage.py fakestudies -n 3
        /app/manage.py fakefiles
        ;;
    *)
        echo "Will not pre-populate database"
        ;;
esac

/app/manage.py setup_permissions

# Make an admin user
echo "from django.contrib.auth import get_user_model;
from django.contrib.auth.models import Group;
from django.db.utils import IntegrityError;
User = get_user_model(); 
print('making superuser');
try:
    User.objects.create_superuser('devadmin', 'admin@myproject.com', 'devadmin')
except IntegrityError:
    print('superuser already exists')
try:
    user = User.objects.get(username='devadmin')
    user.groups.add(Group.objects.get(name='Administrators'))
    user.save()
except Exception as err:
    print(f'Problem occurred when adding devadmin to Administrators: {err}')
" | python manage.py shell

exec /app/manage.py runserver 0.0.0.0:8080
