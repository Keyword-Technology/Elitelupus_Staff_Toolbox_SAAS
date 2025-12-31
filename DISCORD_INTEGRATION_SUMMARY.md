# Discord Integration Summary

## What Was Added

I've successfully added Discord bot functionality and user status tracking to your Elitelupus Staff Toolbox. Here's a complete overview of the changes:

## New Features

### 1. Discord Status Monitoring
- Real-time tracking of staff member Discord presence
- Status types: Online (🟢), Idle (🟡), Do Not Disturb (🔴), Offline (⚫)
- Custom status and activity tracking
- Automatic status updates via Discord bot

### 2. Staff Roster Integration
- Discord status now displays on the staff roster page
- Visual indicators with color-coded badges
- Shows custom status messages and current activities
- Only displays for staff with linked Discord accounts

## Files Modified

### Backend
1. **requirements.txt**
   - Added `discord.py>=2.3.0`

2. **apps/staff/models.py**
   - Added Discord status fields:
     - `discord_status` (online/idle/dnd/offline)
     - `discord_custom_status` (custom status message)
     - `discord_activity` (current game/activity)
     - `discord_status_updated` (last update timestamp)

3. **apps/staff/discord_service.py** (NEW)
   - Discord bot service for monitoring staff presence
   - Handles real-time presence updates
   - Manages guild member status tracking
   - Provides sync functions for manual updates

4. **apps/staff/serializers.py**
   - Updated to include Discord status fields in API responses

5. **apps/staff/views.py**
   - Added `DiscordStatusSyncView` - Manual sync endpoint
   - Added `DiscordBotStatusView` - Check bot health

6. **apps/staff/urls.py**
   - Added `/api/staff/discord/sync/` - Trigger status sync
   - Added `/api/staff/discord/status/` - Check bot status

7. **apps/staff/tasks.py**
   - Added `sync_discord_statuses_task` - Celery task for periodic updates

8. **config/settings.py**
   - Added `DISCORD_BOT_TOKEN` configuration
   - Added `DISCORD_GUILD_ID` configuration

9. **.env.example**
   - Added Discord bot environment variables

10. **apps/staff/migrations/0003_add_discord_status_fields.py** (NEW)
    - Database migration for Discord status fields

### Frontend
1. **components/staff/DiscordStatusBadge.tsx** (NEW)
   - Reusable Discord status badge component
   - Color-coded status indicators
   - Optional custom status/activity display

2. **app/dashboard/staff/page.tsx**
   - Added Discord status column to staff roster table
   - Updated interface to include Discord status fields
   - Integrated DiscordStatusBadge component

### Documentation
1. **DISCORD_BOT_SETUP.md** (NEW)
   - Complete setup guide for Discord bot
   - Step-by-step configuration instructions
   - Troubleshooting tips
   - Security best practices

## Setup Required

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
python manage.py migrate staff
```

### 3. Configure Discord Bot
Follow the instructions in `DISCORD_BOT_SETUP.md`:
1. Create Discord Application in Developer Portal
2. Create Bot User and get token
3. Enable required intents (Presence, Server Members)
4. Add bot to your Discord server
5. Get your Discord Server (Guild) ID

### 4. Update Environment Variables
Add to your `.env` file:
```env
# Discord Bot for Staff Status Monitoring
DISCORD_BOT_TOKEN=your-bot-token-here
DISCORD_GUILD_ID=your-server-id-here
```

### 5. Configure Celery Beat (Optional)
For automatic status updates every 2 minutes, add this Celery Beat task:
- Task: `apps.staff.tasks.sync_discord_statuses_task`
- Interval: 120 seconds (2 minutes)

## API Endpoints

### Check Bot Status
```http
GET /api/staff/discord/status/
Authorization: Bearer <jwt_token>
```

Response:
```json
{
  "is_running": true,
  "guild_id": "1234567890"
}
```

### Manual Sync
```http
POST /api/staff/discord/sync/
Authorization: Bearer <jwt_token>
```

Response:
```json
{
  "message": "Discord status sync completed successfully"
}
```

### Staff Roster (includes Discord status)
```http
GET /api/staff/roster/
Authorization: Bearer <jwt_token>
```

Response includes:
```json
{
  "results": [
    {
      "id": 1,
      "username": "staff_member",
      "discord_id": "123456789",
      "discord_status": "online",
      "discord_custom_status": "Playing Garry's Mod",
      "discord_activity": "Garry's Mod",
      "discord_status_updated": "2024-01-01T12:00:00Z",
      ...
    }
  ]
}
```

## Frontend Display

The Discord status is automatically displayed on the staff roster page with:
- Color-coded status badges (Green/Yellow/Red/Gray)
- Custom status messages
- Current activity/game information
- "Not linked" message for staff without Discord IDs

## Testing

1. **Start the bot** (it starts automatically with Django when configured)
2. **Check bot status**: Visit `/api/staff/discord/status/`
3. **Trigger manual sync**: POST to `/api/staff/discord/sync/`
4. **View roster**: Check the staff roster page for Discord status indicators

## Troubleshooting

### Bot Not Connecting
- Verify `DISCORD_BOT_TOKEN` is correct
- Ensure bot has required intents enabled
- Check bot has access to your server

### Status Not Updating
- Verify bot is running: `GET /api/staff/discord/status/`
- Check Celery worker is running
- Manually trigger sync: `POST /api/staff/discord/sync/`

### No Status Showing
- Ensure staff members have `discord_id` set in roster
- Check Discord IDs are valid user IDs (not usernames)
- Verify bot can see members (Server Members intent required)

## Security Notes

1. **Never commit bot token** to version control
2. **Use environment variables** for sensitive data
3. **Restrict bot permissions** to minimum required
4. **Monitor bot activity** in Discord audit logs
5. **Regenerate token** if compromised

## Next Steps

1. Install dependencies and run migration
2. Follow `DISCORD_BOT_SETUP.md` for Discord configuration
3. Add environment variables to `.env`
4. Restart Django application
5. Configure Celery Beat for automatic updates
6. Test bot connection and status display

## Additional Features You Can Add

- Add Discord notification system for staff actions
- Implement voice channel tracking
- Add Discord role synchronization
- Create Discord slash commands for staff tools
- Add Discord server invite link to staff profile

## Support

For detailed setup instructions, see `DISCORD_BOT_SETUP.md`
