# Steam Profile Lookup - Quick Start Guide

## How to Use

### 1. Access the Templates Page
Navigate to: **Dashboard → Templates**

### 2. Enter Steam ID
In the "Steam Profile Lookup" section:
- Enter any Steam ID format:
  - Steam64: `76561197984856085`
  - Steam ID: `STEAM_0:1:12345678`
  - Steam3: `[U:1:24691357]`
  - Profile URL: `https://steamcommunity.com/profiles/76561197984856085`

### 3. Click Lookup or Press Enter
The system will:
- Convert the ID to all formats
- Fetch data from Steam API
- Check for VAC/game bans
- Track the search
- Show inline summary

### 4. View Quick Summary
Inline display shows:
- Avatar and name
- Steam ID formats
- Ban badges (if any)
- "View Full Profile" button

### 5. Open Full Profile
Click "View Full Profile" to see:

#### Profile Section
- Full avatar
- All Steam ID formats
- Account level
- Location
- Account creation date
- Privacy status
- Direct link to Steam profile

#### Bans & Restrictions
- VAC bans counter
- Game bans counter
- Community ban status
- Trade ban status
- Days since last ban
- Visual warnings (red = banned, green = clean)

#### Recent Changes (if any)
- Highlighted yellow alert box
- Shows what changed:
  - Name changes (Old → New)
  - New bans added
  - Profile visibility changes

#### Search Statistics
- How many times this profile was searched
- When it was first searched
- Who last searched it
- Last search timestamp

#### Related Refund Requests
- All refund templates linked to this Steam ID
- Shows:
  - Ticket number
  - Status badge (pending/approved/denied/completed)
  - Player IGN
  - Items lost
  - Who created it
  - When it was created

#### Search History
- Timeline of past searches
- Each entry shows:
  - When searched
  - Who searched
  - Name at that time
  - Ban counts
  - "Changed" indicator if profile changed

### 6. Use in Templates
After looking up a profile, you can use these variables in refund templates:
- `{steam_id}` - Replaced with STEAM_0:X:XXXXX
- `{steam_id64}` - Replaced with 17-digit Steam64
- `{steam_name}` - Replaced with current persona name
- `{profile_url}` - Replaced with Steam profile URL

## Understanding Ban Indicators

### VAC Bans
- **Red badge**: Player has VAC ban(s)
- **Number**: How many VAC bans
- **Warning**: Shows days since last ban
- **Impact**: Permanent, cannot be removed

### Game Bans
- **Red badge**: Player has game ban(s)
- **Number**: How many game bans
- **Source**: Anti-cheat systems (e.g., GTA V, Rust)
- **Duration**: May be permanent or temporary

### Community Ban
- **Red "Banned"**: Cannot interact with Steam Community
- **Reason**: Inappropriate behavior, scamming, etc.
- **Visibility**: Profile may be restricted

### Trade Ban
- **Status**: "None" (clean) or ban type
- **Impact**: Cannot trade items
- **Reason**: Fraud, chargebacks, policy violations

## Color Coding

### Profile Status
- 🟢 **Green**: Clean account, no restrictions
- 🔴 **Red**: Has bans or restrictions
- 🟡 **Yellow**: Changes detected since last search
- ⚪ **Gray**: Limited account or private profile

### Template Status
- 🟢 **Green**: Approved
- 🔴 **Red**: Denied
- 🔵 **Blue**: Completed
- 🟡 **Yellow**: Pending

## Change Detection

The system automatically detects:
- **Name Changes**: If persona name is different from last search
- **New Bans**: If VAC/game ban count increased
- **Privacy Changes**: If profile visibility changed

### Example Change Alert:
```
⚠️ Changes Detected Since Last Search
Persona name: OldName → NewName
VAC bans: 0 → 1
```

## Search Statistics

### Total Searches
- Counts every lookup of this Steam ID
- Helps identify frequently searched profiles
- Useful for tracking repeat offenders

### First Searched
- When this profile was first looked up
- Relative time format: "3 days ago"
- Helps understand how long you've been tracking someone

### Last Searched By
- Shows which staff member last searched
- Useful for coordination
- Visible to all staff members

## Related Templates Feature

### Automatic Linking
When a Steam ID appears in refund requests:
- System automatically links the profile
- All historical requests are shown
- Quick overview of player history

### Benefits
- See if player has multiple refund requests
- Check status of previous requests
- Identify patterns (e.g., frequent requests)
- Make informed decisions

### Example Use Case
```
Player requests refund for "lost items"
→ Search their Steam ID
→ See they have 3 previous refund requests
→ 2 were approved, 1 denied
→ Make decision based on history
```

## Admin View

Admins can access extended features at `/admin/templates_manager/steamprofilesearch/`:

### Search Records Dashboard
- View all searched profiles
- Sort by search count
- Filter by:
  - VAC bans
  - Game bans
  - Community banned
  - Private profiles
- Search by Steam ID or name

### Bulk Analysis
- Export search data
- Identify most searched profiles
- Track ban trends over time
- Monitor staff search activity

## Tips & Best Practices

### 1. Always Search Before Processing Refunds
- Check ban history
- Review past refund requests
- Look for suspicious patterns

### 2. Note Changes
- If name changed recently: potential red flag
- If new bans: investigate timing
- If multiple refunds: review pattern

### 3. Use Search History
- See how long profile has been tracked
- Check if other staff searched before
- Look for consistency in profile data

### 4. Monitor Related Templates
- Check approval/denial ratio
- Look for similar items in past requests
- Identify repeat requesters

### 5. Cross-Reference
- Use Steam64 to check server logs
- Look up profile on Steam
- Verify information matches

## Common Issues & Solutions

### Profile Not Found
- **Cause**: Invalid Steam ID or private profile
- **Solution**: Verify ID format, check Steam profile visibility

### No Ban Data
- **Cause**: Steam API not responding or rate limited
- **Solution**: Try again in a few minutes

### Missing History
- **Cause**: First time this profile is searched
- **Solution**: Normal for new searches, history will build up

### No Related Templates
- **Cause**: Profile hasn't been used in refund requests yet
- **Solution**: Normal, templates appear when Steam ID is used

## Keyboard Shortcuts

- **Enter**: Submit lookup (when input focused)
- **Escape**: Close modal (when modal open)
- **Click outside**: Close modal

## Mobile Optimization

The interface is fully responsive:
- Touch-friendly buttons
- Scrollable containers
- Readable text sizes
- Optimized layout for small screens

## Privacy & Security

### What's Tracked
✅ Steam ID and profile data
✅ Who searched and when
✅ Changes to profile over time
✅ Related refund requests

### What's NOT Tracked
❌ Private messages
❌ Friends list details
❌ Inventory items
❌ Game playtime (unless added to Steam by user)

### Data Access
- All authenticated staff can search
- Search history visible to all staff
- Admin has additional analytics
- Data stored securely in database

## Need Help?

Contact system administrators if:
- Steam API is not working
- Search counts seem incorrect
- Changes not being detected
- Profile data is outdated

## Future Features Coming Soon

- [ ] Export search history to CSV
- [ ] Advanced ban analytics
- [ ] Automated alerts for new bans
- [ ] Game server log integration
- [ ] Bulk Steam ID lookup
- [ ] Search within results
- [ ] Custom notes on profiles
- [ ] Tag system for profiles
