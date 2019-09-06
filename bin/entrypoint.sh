#!/bin/bash
if [[ -n $VAULT_ADDR ]] && [[ -n $VAULT_ROLE ]]; then
    vault login -method=aws role=$VAULT_ROLE 2>&1 | grep authent

    # Build db connection string
    if [[ -n $PG_HOST ]] && [[ -n $PG_NAME ]] && [[ -n $PG_SECRET ]]; then
        echo "Load postgres connection from vault"
        secrets=$(vault read -format=json ${PG_SECRET} | jq -c '.')
        user=$(echo ${secrets} | jq -r '.data.user')
        pass=$(echo ${secrets} | jq -r '.data.password')

        export PG_USER=$user
        export PG_PASS=$pass
    fi
fi

# Try to load any database secrets, these will override the above
if [[ -n $DATABASE_SECRETS]] ; then
    aws s3 cp $DATABASE_SECRETS ./database.env
    source ./database.env
    rm ./database.env
fi

# This will export our secrets from S3 into our environment
echo "Getting studies from $CAVATICA_SECRETS"
aws s3 cp $CAVATICA_SECRETS ./cavatica.json
echo "Found the following variables to export:"
cat cavatica.json | jq -r 'to_entries|.[].key'
for s in $(cat cavatica.json | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" ); do
    export $s
done

python manage.py syncstudies --api $DATASERVICE_URL
/app/manage.py migrate
exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
