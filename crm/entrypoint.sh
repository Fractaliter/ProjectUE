#!/usr/bin/env bash

echo "🌍 Środowisko: $ENVIRONMENT"
echo "⏳ Czekam na bazę danych..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.5
done

echo "✅ Migracje..."
python manage.py migrate

echo "🔐 Tworzę superusera (jeśli nie istnieje)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from webapp.models import UserProfile
User = get_user_model()
username = '$DJANGO_SUPERUSER_USERNAME'
email = '$DJANGO_SUPERUSER_EMAIL'
password = '$DJANGO_SUPERUSER_PASSWORD'

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username, email, password)
    UserProfile.objects.create(user=user)
"

echo "👤 Tworzę profile dla pozostałych użytkowników (jeśli brak)..."
python manage.py shell -c "
from django.contrib.auth.models import User
from webapp.models import UserProfile

for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
"

if [ "$ENVIRONMENT" = "production" ]; then
  echo "🚀 Uruchamiam Gunicorn (produkcja)"
  gunicorn crm.wsgi:application --bind 0.0.0.0:8000
else
  echo "🚧 Uruchamiam Django dev server (lokalnie)"
  python manage.py runserver 0.0.0.0:8000
fi
