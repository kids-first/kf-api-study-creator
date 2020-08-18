#!/bin/ash
# Try to load any database secrets, these will override the above
if [ -n $DATABASE_SECRETS ]; then
    aws s3 cp $DATABASE_SECRETS ./database.env
    source ./database.env
    export $(cut -d= -f1 ./database.env)
    rm ./database.env
fi

# Try to load auth0 secrets from S3
if [ -n $AUTH0_SECRETS ]; then
    aws s3 cp $AUTH0_SECRETS ./auth0.env
    source ./auth0.env
    export $(cut -d= -f1 ./auth0.env)
    rm ./auth0.env
fi

# Try to load general settings from S3
if [ -n $SETTINGS ]; then
    aws s3 cp $SETTINGS ./settings.env
    source ./settings.env
    export $(cut -d= -f1 ./settings.env)
    rm ./settings.env
fi

# This will export our secrets from S3 into our environment
if [ -n $CAVATICA_SECRETS ]; then
    aws s3 cp $CAVATICA_SECRETS ./cavatica.env
    source ./cavatica.env
    export $(cut -d= -f1 ./cavatica.env)
    rm ./cavatica.env
fi

if [[ -n $CAVATICA_VOLUMES ]]; then
    echo "Loading Cavatica volume credentials from S3"
    aws s3 cp $CAVATICA_VOLUMES ./cavatica_volumes.env
    source ./cavatica_volumes.env
    export $(cut -d= -f1 ./cavatica_volumes.env)
    rm ./cavatica_volumes.env
fi

if [[ -n $EMAIL ]]; then
    echo "Loading email credentials from S3"
    aws s3 cp $EMAIL ./email.env
    source ./email.env
    export $(cut -d= -f1 ./email.env)
    rm ./email.env
fi

if $WORKER ; then
    supervisord -c  /etc/supervisor/conf.d/worker.conf
elif [[ $1 = scheduler ]]; then
    /app/manage.py schedule_jobs
    supervisord -c  /etc/supervisor/conf.d/scheduler.conf
else
    /app/manage.py migrate
    /app/manage.py setup_permissions
    exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
fi
