#!/bin/bash
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
        # python manage.py faketeststudies 
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
    "UAT")
        echo Will create user testing data for $PI
        /app/manage.py fakestudies -n=6
        /app/manage.py uastudies -pi=$PI
        echo 'Loading fake users'
        /app/manage.py loaddata creator_users.json
        echo 'Loading CBTTC files to SD_YN6HB8C5'
        /app/manage.py uatfiles -studyId=SD_BHJXBDQK -destId=SD_YN6HB8C5
        echo 'Loading SD_DZTB5HRR files to SD_8LEDFLQZ5'
        /app/manage.py uatfiles -studyId=SD_DZTB5HRR -destId=SD_8LEDFLQZ
        echo 'Loading Chung: SD_46SK55A3 files to SD_KZRADNFE'
        /app/manage.py loaddata fake_chung_files.json
        ;;
    *)
        echo "Will not pre-populate database"
        ;;
esac

# Make an admin user
echo "from django.contrib.auth import get_user_model;
User = get_user_model(); 
if User.objects.count() == 0:
    User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python manage.py shell

exec /app/manage.py runserver 0.0.0.0:8080
