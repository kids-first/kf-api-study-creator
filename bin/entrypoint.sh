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

python manage.py syncstudies --api $DATASERVICE_URL
/app/manage.py migrate
exec gunicorn creator.wsgi:application -b 0.0.0.0:80 --access-logfile - --error-logfile - --workers 4
