#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Send Discord notification after successful startup
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    echo "📢 Sending Discord startup notification..."
    python send_discord_notification.py || echo "⚠️  Discord notification failed, continuing anyway..."
fi

echo "Starting Daphne server..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
