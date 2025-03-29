#!/bin/sh

echo "🌍 Środowisko: $ENVIRONMENT"
echo "⏳ Czekam na bazę danych..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.5
done

echo "✅ Migracje..."
python manage.py migrate

# tylko jeśli user jeszcze nie istnieje
echo "🔐 Tworzę superusera (jeśli nie istnieje)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        '$DJANGO_SUPERUSER_USERNAME',
        '$DJANGO_SUPERUSER_EMAIL',
        '$DJANGO_SUPERUSER_PASSWORD'
    )
"

if [ "$ENVIRONMENT" = "production" ]; then
  echo "🚀 Uruchamiam Gunicorn (produkcja)"
  gunicorn crm.wsgi:application --bind 0.0.0.0:8000
else
  echo "🚧 Uruchamiam Django dev server (lokalnie)"
  python manage.py runserver 0.0.0.0:8000
fi

