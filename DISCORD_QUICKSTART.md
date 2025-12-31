# Quick Start: Discord Bot Setup

## Prerequisites
- Discord account with admin access to your server
- Backend dependencies installed (`pip install -r requirements.txt`)
- Database migrated (`python manage.py migrate`)

## 5-Minute Setup

### Step 1: Create Discord Bot (2 minutes)
1. Go to https://discord.com/developers/applications
2. Click "New Application" → Name it "Elitelupus Staff Monitor"
3. Go to "Bot" section → Click "Add Bot"
4. Click "Reset Token" → **Copy the token** (save it!)
5. Scroll down to "Privileged Gateway Intents":
   - ✅ Enable "Server Members Intent"
   - ✅ Enable "Presence Intent"
6. Click "Save Changes"

### Step 2: Add Bot to Server (1 minute)
1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions: "View Channels"
4. Copy the generated URL
5. Open URL in browser → Select your server → Authorize

### Step 3: Get Server ID (30 seconds)
1. Open Discord → Enable Developer Mode:
   - User Settings → Advanced → Developer Mode (ON)
2. Right-click your server icon → "Copy Server ID"

### Step 4: Configure Backend (1 minute)
1. Open your `.env` file
2. Add these lines:
```env
DISCORD_BOT_TOKEN=paste-your-bot-token-here
DISCORD_GUILD_ID=paste-your-server-id-here
```
3. Save the file

### Step 5: Restart & Test (30 seconds)
```bash
# Restart Django
# The bot will start automatically

# Test bot status
curl http://localhost:8000/api/staff/discord/status/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Should return: {"is_running": true, "guild_id": "..."}
```

## Verification Checklist
- [ ] Bot appears online in your Discord server
- [ ] Bot status API returns `"is_running": true`
- [ ] Staff roster page shows Discord status column
- [ ] Staff with Discord IDs show their status

## Common Issues

### Bot shows offline in Discord
- **Solution**: Check `DISCORD_BOT_TOKEN` is correct, restart Django

### "Bot not running" error
- **Solution**: Verify intents are enabled in Discord Developer Portal

### No status displayed on roster
- **Solution**: Ensure staff members have `discord_id` set in database

## What Happens Now?

1. **Automatic Monitoring**: Bot tracks staff Discord presence in real-time
2. **Visual Display**: Staff roster shows colored status badges
3. **Periodic Updates**: Celery task syncs statuses every 2 minutes (if configured)
4. **Manual Sync**: Use API endpoint to force immediate update

## Status Colors

- 🟢 **Green**: Online
- 🟡 **Yellow**: Idle/Away
- 🔴 **Red**: Do Not Disturb
- ⚫ **Gray**: Offline or not linked

## Next Steps

1. Add Discord IDs to your staff roster
2. Configure Celery Beat for automatic updates
3. Check the full documentation in `DISCORD_BOT_SETUP.md`

## Need Help?

- Full setup guide: `DISCORD_BOT_SETUP.md`
- Integration details: `DISCORD_INTEGRATION_SUMMARY.md`
- Troubleshooting: See "Troubleshooting" section in setup guide
