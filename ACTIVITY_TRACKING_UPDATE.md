# Discord Bot Now Optional - In-App Activity Tracking Added

## What Changed

The Discord bot is now **completely optional**. If you don't configure it, the system automatically falls back to tracking staff activity within your application instead.

## New Features

### 1. In-App Activity Tracking (Default)
- Tracks when staff are active in your application
- Shows "Active in App" status with timestamp
- Updates automatically as staff use the system
- No external dependencies required

### 2. Automatic Fallback
- If Discord bot is not configured → Uses in-app tracking
- If Discord bot IS configured → Uses Discord status
- Seamless switching between modes

## How It Works

### Without Discord Bot (Default)
When staff members use your application:
1. **Middleware tracks activity** - Every request updates `last_seen` timestamp
2. **Auto-marks inactive** - Users inactive for 5+ minutes are marked offline
3. **Frontend displays**:
   - 🟢 "Active in App" (if seen in last 5 minutes)
   - ⚫ "2m ago", "1h ago", "2d ago" (if inactive)
   - "No activity" (if never seen)

### With Discord Bot (Optional)
If you configure the Discord bot:
- Shows real Discord status (Online/Idle/DND/Offline)
- Displays custom status and activity
- Falls back to in-app tracking if Discord unavailable

## Database Changes

New fields added to `StaffRoster` model:
- `last_seen` - Timestamp of last activity
- `is_active_in_app` - Boolean for active/inactive status

## Setup Instructions

### Option 1: Use In-App Tracking (No Setup Required)

Just run the migration and it works:
```bash
cd backend
python manage.py migrate staff
```

**That's it!** The middleware will automatically track staff activity.

### Option 2: Enable Discord Bot (Optional)

Follow the setup in `DISCORD_BOT_SETUP.md` if you want Discord integration.

## Updated Files

### Backend
1. **apps/staff/models.py**
   - Added `last_seen` and `is_active_in_app` fields
   - Updated comments to show Discord is optional

2. **apps/staff/middleware.py** (NEW)
   - Tracks staff activity on every request
   - Updates `last_seen` timestamp automatically
   - Links activity to staff roster entries

3. **apps/staff/serializers.py**
   - Added `last_seen_display` - Human-readable time (e.g., "2m ago")
   - Added `is_active_display` - Boolean for active in last 5 min
   - Updated to include new activity fields

4. **apps/staff/views.py**
   - Updated to check if Discord bot is configured
   - Returns helpful messages when bot not set up
   - Gracefully handles missing configuration

5. **apps/staff/tasks.py**
   - Updated Discord sync to check configuration first
   - Added `mark_inactive_staff` task (runs every 5 minutes)
   - Skips Discord sync if not configured

6. **config/settings.py**
   - Added `StaffActivityMiddleware` to track activity
   - Updated Discord settings to show they're optional

7. **apps/staff/migrations/0004_add_activity_tracking.py** (NEW)
   - Migration for new activity tracking fields

### Frontend
1. **app/dashboard/staff/page.tsx**
   - Changed column header to "Activity Status"
   - Shows Discord status if available
   - Falls back to in-app activity if not
   - Displays human-readable timestamps

## Display Logic

The frontend now shows status in this priority order:

1. **Discord Status** (if Discord ID linked AND status available)
   - 🟢 Online / 🟡 Idle / 🔴 DND / ⚫ Offline
   - Shows custom status/activity

2. **Active in App** (if seen in last 5 minutes)
   - 🟢 "Active in App" with pulsing indicator
   - Shows "Just now", "2m ago", etc.

3. **Recently Active** (if has last_seen timestamp)
   - ⚫ Shows time since last activity
   - "5m ago", "2h ago", "3d ago"

4. **No Activity** (if never seen)
   - Gray "No activity" text

## API Changes

### Staff Roster Response
Now includes activity tracking fields:

```json
{
  "id": 1,
  "username": "staff_member",
  "discord_status": null,  // null if Discord not configured
  "last_seen": "2024-01-01T12:34:56Z",
  "is_active_in_app": true,
  "last_seen_display": "2m ago",
  "is_active_display": true,
  ...
}
```

### Discord Bot Status Endpoint
Returns configuration status:

```http
GET /api/staff/discord/status/
```

**Without Bot Configured:**
```json
{
  "configured": false,
  "is_running": false,
  "guild_id": null,
  "message": "Discord bot is not configured. Using in-app activity tracking."
}
```

**With Bot Configured:**
```json
{
  "configured": true,
  "is_running": true,
  "guild_id": "123456789"
}
```

## Migration Steps

### 1. Update Dependencies
```bash
cd backend
pip install -r requirements.txt  # Already includes discord.py
```

### 2. Run Migrations
```bash
python manage.py migrate staff
```

This creates:
- Discord status fields (from previous migration)
- Activity tracking fields (new)

### 3. Restart Application
```bash
# Restart Django
# Middleware will start tracking automatically
```

### 4. (Optional) Configure Celery Beat

Add this task to mark inactive users:
- **Task**: `apps.staff.tasks.mark_inactive_staff`
- **Interval**: Every 5 minutes
- **Purpose**: Marks users as inactive if not seen in 5 minutes

## Testing

### Test In-App Activity Tracking
1. Login as a staff member
2. View the staff roster page
3. Your status should show "Active in App"
4. Wait 5 minutes without activity
5. Status changes to "5m ago"

### Test Discord Integration (if configured)
1. Set `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID`
2. Restart Django
3. Check bot status: `GET /api/staff/discord/status/`
4. Should return `"configured": true, "is_running": true`

## Celery Beat Schedule (Optional)

Add these tasks for best experience:

```python
CELERY_BEAT_SCHEDULE = {
    # Discord status sync (only if bot configured)
    'sync-discord-statuses': {
        'task': 'apps.staff.tasks.sync_discord_statuses_task',
        'schedule': 120.0,  # Every 2 minutes
    },
    # Mark inactive staff (for in-app tracking)
    'mark-inactive-staff': {
        'task': 'apps.staff.tasks.mark_inactive_staff',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

## Troubleshooting

### Activity not updating
- Verify middleware is enabled in settings
- Check that staff member has roster entry
- Ensure user is authenticated

### Discord status not showing
- Check `GET /api/staff/discord/status/` returns configured=true
- Verify Discord bot token and guild ID are set
- See `DISCORD_BOT_SETUP.md` for full troubleshooting

### "No activity" for all staff
- Run migration: `python manage.py migrate staff`
- Activity tracking starts after migration
- Staff need to use the app to be tracked

## Benefits

### Without Discord Bot
✅ No external dependencies
✅ No bot setup required
✅ Works immediately
✅ Tracks actual app usage
✅ Zero maintenance

### With Discord Bot
✅ See staff Discord status
✅ Custom status messages
✅ Activity/game tracking
✅ Works even when not using app
✅ More detailed presence info

## Summary

You now have **two options** for tracking staff presence:

1. **Default**: In-app activity tracking (automatic, no setup)
2. **Optional**: Discord bot integration (more features, requires setup)

The system automatically uses whichever is available, with in-app tracking as the reliable fallback. No configuration changes needed for basic functionality!
