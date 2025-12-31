# Discord Bot Setup Guide

This guide will help you set up the Discord bot for monitoring staff member presence and status.

## Features

- Real-time Discord status monitoring (Online, Idle, DND, Offline)
- Custom status and activity tracking
- Automatic status updates for all staff members
- Periodic background sync via Celery
- Integration with staff roster display

## Prerequisites

1. Discord account with admin permissions on your server
2. Discord Developer Portal access
3. Python 3.8+ with discord.py library
4. Redis (for Celery tasks)

## Step 1: Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Elitelupus Staff Monitor")
4. Click "Create"

## Step 2: Create Bot User

1. In your application, go to the "Bot" section
2. Click "Add Bot" and confirm
3. Under "Token", click "Reset Token" and copy it
   - **IMPORTANT**: Keep this token secret!
   - Save it to your `.env` file as `DISCORD_BOT_TOKEN`

## Step 3: Configure Bot Permissions

### Required Privileged Gateway Intents

In the "Bot" section, enable these intents:
- ✅ **Server Members Intent**
- ✅ **Presence Intent**
- ✅ **Message Content Intent** (optional, for future features)

### Bot Permissions

In the "OAuth2 > URL Generator" section:
1. Select scopes:
   - `bot`
2. Select bot permissions:
   - View Channels
   - Read Messages/View Channels

Generate the URL and use it to invite the bot to your server.

## Step 4: Get Your Discord Server (Guild) ID

1. Enable Developer Mode in Discord:
   - User Settings > Advanced > Developer Mode
2. Right-click your server icon
3. Click "Copy Server ID"
4. Save it to your `.env` file as `DISCORD_GUILD_ID`

## Step 5: Environment Configuration

Add these variables to your `.env` file:

```env
# Discord Bot Settings
DISCORD_BOT_TOKEN=your-bot-token-here
DISCORD_GUILD_ID=your-server-id-here

# Discord OAuth (if not already configured)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
```

## Step 6: Link Staff Members to Discord

Staff members need their Discord IDs added to the roster. There are two ways:

### Method 1: Manual Entry
1. Have staff member enable Developer Mode in Discord
2. Right-click their profile > Copy User ID
3. Add to Google Sheets roster or database

### Method 2: OAuth Linking (Recommended)
1. Staff member logs in via Discord OAuth
2. System automatically links Discord ID
3. Updates roster with Discord information

## Step 7: Database Migration

Run the migration to add Discord status fields:

```bash
cd backend
python manage.py makemigrations staff
python manage.py migrate staff
```

## Step 8: Install Dependencies

```bash
cd backend
pip install discord.py>=2.3.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Step 9: Start the Discord Bot

The bot will start automatically when the Django application starts. However, you can also start it manually via Django shell:

```python
python manage.py shell
```

```python
from apps.staff.discord_service import start_discord_bot
import asyncio

asyncio.run(start_discord_bot())
```

## Step 10: Configure Celery Beat Schedule

The Discord status sync task should run periodically. Add this to your Celery Beat schedule:

1. Go to Django Admin: `/admin/django_celery_beat/periodictask/`
2. Add a new periodic task:
   - **Name**: "Discord Status Sync"
   - **Task**: `apps.staff.tasks.sync_discord_statuses_task`
   - **Interval**: Every 2 minutes (or as desired)
   - **Enabled**: ✅

Or configure in settings:

```python
# config/settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-discord-statuses': {
        'task': 'apps.staff.tasks.sync_discord_statuses_task',
        'schedule': 120.0,  # Every 2 minutes
    },
}
```

## Usage

### API Endpoints

1. **Check Bot Status**
   ```
   GET /api/staff/discord/status/
   ```
   Returns: `{ "is_running": true, "guild_id": "123456789" }`

2. **Manual Sync**
   ```
   POST /api/staff/discord/sync/
   ```
   Triggers immediate status sync for all staff members

3. **Staff Roster** (includes Discord status)
   ```
   GET /api/staff/roster/
   ```
   Returns staff list with Discord status fields:
   - `discord_status`: online, idle, dnd, offline
   - `discord_custom_status`: User's custom status message
   - `discord_activity`: Current activity/game
   - `discord_status_updated`: Last update timestamp

### Frontend Display

Discord status is automatically displayed on the staff roster page with color-coded badges:
- 🟢 **Online** (Green)
- 🟡 **Idle** (Yellow)
- 🔴 **Do Not Disturb** (Red)
- ⚫ **Offline** (Gray)

## Troubleshooting

### Bot Not Connecting

1. **Check token**: Ensure `DISCORD_BOT_TOKEN` is correct
2. **Check intents**: Verify Presence and Server Members intents are enabled
3. **Check permissions**: Ensure bot has "View Channels" permission
4. **Check logs**: Look for errors in Django logs

```bash
docker-compose logs backend | grep discord
```

### Status Not Updating

1. **Check if bot is running**:
   ```bash
   curl http://localhost:8000/api/staff/discord/status/
   ```

2. **Manual sync**:
   ```bash
   curl -X POST http://localhost:8000/api/staff/discord/sync/ \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Check Celery worker**:
   ```bash
   docker-compose logs celery
   ```

### Bot Can't See Members

1. Verify bot has "Server Members Intent" enabled
2. Ensure bot is in the correct server (check `DISCORD_GUILD_ID`)
3. Bot needs to be added to server with proper permissions

### Rate Limiting

Discord has rate limits. If you have many staff members:
- Increase sync interval (e.g., 5 minutes instead of 2)
- Implement exponential backoff in service
- Monitor Discord API rate limit headers

## Production Deployment

### Docker

The Discord bot service will run automatically with your Django application. Ensure:

1. Environment variables are set in `.env`
2. Redis is running (required for Celery)
3. Celery worker and beat are running

```bash
docker-compose up -d
```

### Systemd Service (Manual Deployment)

If running without Docker, ensure the bot starts with Django:

```ini
[Unit]
Description=Elitelupus Staff Toolbox
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/elitelupus-staff-toolbox/backend
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/opt/elitelupus-staff-toolbox/venv/bin/daphne -b 0.0.0.0 -p 8000 config.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Best Practices

1. **Never commit bot token** to version control
2. **Use environment variables** for sensitive data
3. **Restrict bot permissions** to minimum required
4. **Monitor bot activity** in Discord audit logs
5. **Regenerate token** if compromised
6. **Use separate bot** for production and development

## Monitoring

### Check Bot Health

```bash
# Via API
curl http://localhost:8000/api/staff/discord/status/

# Via Django shell
python manage.py shell
```

```python
from apps.staff.discord_service import get_bot_instance
bot = get_bot_instance()
print(f"Running: {bot.is_running}")
print(f"Guild ID: {bot.guild_id}")
```

### Logs

```bash
# All logs
docker-compose logs -f backend

# Discord-specific
docker-compose logs -f backend | grep discord

# Celery tasks
docker-compose logs -f celery
```

## Support

For issues or questions:
- Check the [Discord.py Documentation](https://discordpy.readthedocs.io/)
- Review Django logs for errors
- Ensure all environment variables are set correctly
- Verify bot permissions in Discord Developer Portal

## Updates and Maintenance

### Updating Discord.py

```bash
pip install --upgrade discord.py
```

### Database Schema Changes

If Discord status fields change, create and run migrations:

```bash
python manage.py makemigrations staff
python manage.py migrate staff
```

### Testing Bot Connection

```python
# Django shell
python manage.py shell

from apps.staff.discord_service import get_bot_instance, sync_discord_statuses
import asyncio

bot = get_bot_instance()
if bot.is_running:
    asyncio.run(sync_discord_statuses())
    print("Sync completed!")
else:
    print("Bot is not running")
```
