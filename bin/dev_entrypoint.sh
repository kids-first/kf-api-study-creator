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

/app/manage.py setup_permissions
/app/manage.py setup_test_user

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
        /app/manage.py fakereleases
        ;;
    *)
        echo "Will not pre-populate database"
        ;;
esac

exec /app/manage.py runserver 0.0.0.0:8080
