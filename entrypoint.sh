#!/bin/bash
PRODUCTION_SETTINGS_FILE="/app/routerfleet/production_settings.py"

set -e

if [[ "$COMPOSE_VERSION" != "02d" ]]; then
    echo "ERROR: Please upgrade your docker compose file. Exiting."
    exit 1
fi

if [ -z "$SERVER_ADDRESS" ]; then
    echo "SERVER_ADDRESS environment variable is not set. Exiting."
    exit 1
fi

if [[ "${DATABASE_ENGINE,,}" == "sqlite" ]]; then
    if [[ "$COMPOSE_TYPE" != "no-postgres" ]]; then
        echo "ERROR: Please use 'docker-compose-no-postgres.yml' when using sqlite as DATABASE_ENGINE. Exiting."
        exit 1
    fi
    DATABASES_CONFIG="DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/var/lib/routerfleet_sqlite/routerfleet-db.sqlite3',
        }
    }"
elif [[ "${DATABASE_ENGINE,,}" == "postgres" ]]; then
    if [ -n "$POSTGRES_HOST" ]; then
      if [[ "$COMPOSE_TYPE" != "no-postgres" ]]; then
          echo "ERROR: When using a remote PostgreSQL server, please use 'docker-compose-no-postgres.yml'. Exiting."
          exit 1
      fi
      if [ -z "$POSTGRES_PORT" ]; then
          POSTGRES_PORT="5432"
      fi
    else
        if [[ "$COMPOSE_TYPE" != "with-postgres" ]]; then
            echo "ERROR: Local postgres is selected. Please use 'docker-compose.yml'. Exiting."
            exit 1
        fi
        POSTGRES_HOST="routerfleet-postgres"
        POSTGRES_PORT="5432"
    fi

    if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        echo "POSTGRES_DB, POSTGRES_USER, or POSTGRES_PASSWORD environment variable is not set. Exiting."
        exit 1
    fi
    DATABASES_CONFIG="DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': '$POSTGRES_DB',
            'USER': '$POSTGRES_USER',
            'PASSWORD': '$POSTGRES_PASSWORD',
            'HOST': '$POSTGRES_HOST',
            'PORT': '$POSTGRES_PORT',
        }
    }"
else
    echo "Unsupported DATABASE_ENGINE. Exiting."
    exit 1
fi

DEBUG_VALUE="False"
if [[ "${DEBUG_MODE,,}" == "true" ]]; then
    DEBUG_VALUE="True"
fi

SERVER_HOSTNAME=$(echo $SERVER_ADDRESS | cut -d ':' -f 1)

cat > $PRODUCTION_SETTINGS_FILE <<EOL
DEBUG = $DEBUG_VALUE
ALLOWED_HOSTS = ['routerfleet', '$SERVER_HOSTNAME']
CSRF_TRUSTED_ORIGINS = ['http://routerfleet', 'https://$SERVER_ADDRESS', 'http://$SERVER_ADDRESS']
SECRET_KEY = '$(openssl rand -base64 32)'
$DATABASES_CONFIG
EOL

if [ -n "$TZ" ]; then
    echo "TIME_ZONE = '$TZ'" >> $PRODUCTION_SETTINGS_FILE
fi

if [ ! -f /app_secrets/monitoring_key ]; then
    cat /proc/sys/kernel/random/uuid > /app_secrets/monitoring_key
fi
echo "MONITORING_KEY = '$(cat /app_secrets/monitoring_key)'" >> $PRODUCTION_SETTINGS_FILE


sed -i "/^    path('admin\/', admin.site.urls),/s/^    /    # /" /app/routerfleet/urls.py

exec "$@"
