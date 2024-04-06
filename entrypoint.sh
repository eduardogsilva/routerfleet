#!/bin/bash

set -e

if [ -z "$SERVER_ADDRESS" ]; then
    echo "SERVER_ADDRESS environment variable is not set. Exiting."
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "POSTGRES_PASSWORD environment variable is not set. Exiting."
    exit 1
fi

DEBUG_VALUE="False"
if [[ "${DEBUG_MODE,,}" == "true" ]]; then
    DEBUG_VALUE="True"
fi

cat > /app/routerfleet/production_settings.py <<EOL
DEBUG = $DEBUG_VALUE
ALLOWED_HOSTS = ['routerfleet', '$SERVER_ADDRESS']
CSRF_TRUSTED_ORIGINS = ['http://routerfleet', 'https://$SERVER_ADDRESS']
SECRET_KEY = '$(openssl rand -base64 32)'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'routerfleet',
        'USER': 'routerfleet',
        'PASSWORD': '$POSTGRES_PASSWORD',
        'HOST': 'routerfleet-postgres',
        'PORT': '5432',
    }
}
EOL

if [ -n "$TIMEZONE" ]; then
    echo "TIME_ZONE = '$TIMEZONE'" >> /app/routerfleet/production_settings.py
fi

sed -i "/^    path('admin\/', admin.site.urls),/s/^    /    # /" /app/routerfleet/urls.py

exec "$@"