# Enhanced Steam Profile Lookup - Implementation Summary

## Overview
Implemented comprehensive Steam profile lookup enhancements with detailed tracking, history, and data from multiple sources including Steam API ban information. The system now tracks all searches, detects changes over time, and links Steam profiles to refund templates.

## Backend Changes

### 1. New Models (`apps/templates_manager/models.py`)

#### SteamProfileSearch Model
Tracks Steam profile searches and stores comprehensive profile data:
- **Steam IDs**: `steam_id_64`, `steam_id` (multiple formats)
- **Search Tracking**: `search_count`, `first_searched_at`, `last_searched_at`, `last_searched_by`
- **Profile Data**: `persona_name`, `profile_url`, `avatar_url`, `profile_state`, `real_name`, `location`
- **Extended Data**: `account_created`, `vac_bans`, `game_bans`, `days_since_last_ban`, `community_banned`, `trade_ban`
- **Account Status**: `is_private`, `is_limited`, `level`

#### SteamProfileHistory Model
Tracks changes to Steam profiles over time:
- Links to `SteamProfileSearch` via foreign key
- Stores snapshot of profile data at each search
- `changes_detected` JSON field tracks what changed between searches
- Includes searcher information and timestamp

#### RefundTemplate Model Enhancement
- Added `steam_profile` foreign key linking to `SteamProfileSearch`
- Enables tracking which Steam IDs are associated with refund requests

### 2. Steam Lookup Service (`apps/templates_manager/services.py`)

#### SteamLookupService Class
Comprehensive service for Steam profile lookups:

**Features**:
- Converts between different Steam ID formats (Steam64, STEAM_X:Y:Z, [U:1:XXXXX])
- Fetches data from Steam Web API:
  - Player summaries (name, avatar, profile URL, visibility state, account creation date)
  - Player bans (VAC bans, game bans, community bans, trade restrictions)
- Tracks search statistics (count, first/last search dates, who searched)
- Detects changes between searches (name changes, new bans, profile state changes)
- Retrieves related refund templates
- Returns complete search history

**Methods**:
- `lookup_profile(steam_id, user)` - Main lookup method with full tracking
- `_convert_to_steam_id_64()` - Converts any format to Steam64
- `_convert_to_steam_id()` - Converts Steam64 to STEAM_X:Y:Z
- `_fetch_steam_api_data()` - Gets profile data from Steam API
- `_fetch_ban_data()` - Gets ban information from Steam API
- `_detect_changes()` - Identifies changes since last search
- `_serialize_templates()` - Formats related refund templates
- `_serialize_history()` - Formats search history

### 3. Updated Views (`apps/templates_manager/views.py`)

#### SteamProfileLookupView (Enhanced)
- Now uses `SteamLookupService` for comprehensive data
- Tracks user performing the search
- Returns full profile data including bans, history, and related templates

#### New Views:
- **SteamProfileSearchListView**: List all Steam profile searches with filters
  - Filter by `steam_id_64`
  - Order by search count or date
  - Limit to top 100 results
  
- **SteamProfileSearchDetailView**: Get detailed search record by Steam64
  
- **SteamProfileHistoryListView**: Get search history for a specific profile
  - Requires `steam_id_64` query parameter
  - Returns last 50 searches

### 4. Updated Serializers (`apps/templates_manager/serializers.py`)

#### New Serializers:
- **SteamProfileSearchSerializer**: Serializes search records
- **SteamProfileHistorySerializer**: Serializes history entries
- **SteamProfileSerializer** (Enhanced): Now handles full profile data structure with nested dictionaries

### 5. Admin Interface (`apps/templates_manager/admin.py`)

#### SteamProfileSearchAdmin
- Display: Steam64, name, search count, bans, last search info
- Filters: VAC bans, game bans, community banned, private profiles
- Search: Steam IDs and persona name
- Read-only: Search tracking fields
- Organized fieldsets: Steam IDs, Profile Info, Account Status, Bans, Search Tracking

#### SteamProfileHistoryAdmin
- Display: Search, timestamp, searcher, name, bans, changes indicator
- Filters: Date, VAC bans, game bans
- Search: Steam ID, persona name
- Custom method: `has_changes()` boolean indicator

### 6. Updated URLs (`apps/templates_manager/urls.py`)

New endpoints:
- `POST /api/templates/steam-lookup/` - Enhanced lookup with tracking
- `GET /api/templates/steam-searches/` - List all searches
- `GET /api/templates/steam-searches/<steam_id_64>/` - Get specific search record
- `GET /api/templates/steam-history/?steam_id_64=<id>` - Get search history

### 7. Database Migrations

Generated migration: `0002_steamprofilesearch_steamprofilehistory_and_more.py`
- Creates `SteamProfileSearch` table
- Creates `SteamProfileHistory` table
- Adds `steam_profile` foreign key to `RefundTemplate`

## Frontend Changes

### 1. Enhanced Steam Profile Component (`components/templates/EnhancedSteamProfile.tsx`)

Comprehensive display component featuring:

#### Header Section
- Large avatar display
- Profile name with status badges (Private, Limited)
- Real name display
- Steam ID and Steam64 in monospace font
- Account level and location
- Account creation date
- Link to Steam profile

#### Bans & Restrictions Section
- Visual indicators for VAC bans, game bans, community bans, trade bans
- Color-coded cards (red for bans, green for clean)
- Displays days since last ban if applicable
- Clear "Clean" vs "Banned" status

#### Recent Changes Alert
- Highlighted section if changes detected since last search
- Shows old vs new values for:
  - Persona name changes
  - New VAC/game bans
  - Profile state changes
- Color-coded: red for old value (strikethrough), green for new value

#### Search Statistics
- Total searches counter
- First searched date (relative time)
- Last searched by (username)
- Formatted dates with date-fns

#### Related Refund Requests
- Lists all refund templates associated with this Steam ID
- Shows ticket number with status badge (pending/approved/denied/completed)
- Displays IGN, items lost preview
- Shows who created it and when
- Color-coded status badges

#### Search History
- Chronological list of past searches (last 10)
- Shows persona name at time of search
- Displays VAC/game ban counts
- Indicates if changes were detected
- Shows who searched and when
- Scrollable container with max height

**Styling**: 
- Dark theme consistent with app
- Responsive grid layouts
- Clear visual hierarchy
- Icon integration from Heroicons
- Smooth hover effects

### 2. Updated Templates Page (`app/dashboard/templates/page.tsx`)

#### Updated Interface Types
- `SteamProfileData`: Comprehensive type matching backend response
  - Nested structures for profile, bans, search_stats, changes
  - Arrays for related_templates and search_history

#### New State Management
- `showProfileModal`: Controls enhanced profile modal visibility
- Updated `steamProfile` type to use new `SteamProfileData`

#### Modified Steam Lookup Flow
1. User enters Steam ID
2. Click "Lookup" or press Enter
3. API call to enhanced endpoint
4. Brief profile summary displayed inline
5. "View Full Profile" button opens modal
6. Modal shows `EnhancedSteamProfile` component with all data

#### Inline Profile Summary
Compact view showing:
- Small avatar (48x48)
- Name and Steam ID
- VAC/game ban badges if present
- "View Full Profile" button

#### Modal Implementation
- Full-screen overlay with dark backdrop
- Scrollable container
- Max width 5xl for optimal viewing
- Close button in component
- Outside click to close

#### Template Variable Replacement
Updated to use new profile structure:
- `{steam_id}` → `steamProfile.steam_id`
- `{steam_id64}` → `steamProfile.steam_id_64`
- `{steam_name}` → `steamProfile.profile.name`
- `{profile_url}` → `steamProfile.profile.profile_url`

### 3. Dependencies
- **date-fns**: Added for date formatting (formatDistanceToNow, format)

## API Response Structure

### Enhanced Lookup Response
```json
{
  "steam_id": "STEAM_0:1:12345678",
  "steam_id_64": "76561197984856085",
  "profile": {
    "name": "PlayerName",
    "profile_url": "https://steamcommunity.com/profiles/76561197984856085",
    "avatar_url": "https://avatars.steamstatic.com/...",
    "profile_state": "public|private|friends_only",
    "real_name": "Real Name",
    "location": "US",
    "is_private": false,
    "is_limited": false,
    "level": 42,
    "account_created": "2010-01-01T00:00:00Z"
  },
  "bans": {
    "vac_bans": 0,
    "game_bans": 0,
    "days_since_last_ban": null,
    "community_banned": false,
    "trade_ban": "none"
  },
  "search_stats": {
    "total_searches": 5,
    "first_searched": "2024-01-01T12:00:00Z",
    "last_searched": "2024-01-15T15:30:00Z",
    "last_searched_by": "admin"
  },
  "changes": {
    "persona_name": {
      "old": "OldName",
      "new": "NewName"
    }
  },
  "related_templates": [
    {
      "id": 1,
      "ticket_number": "TICKET-001",
      "status": "pending",
      "player_ign": "PlayerIGN",
      "created_by": "staff_member",
      "created_at": "2024-01-10T10:00:00Z",
      "items_lost": "M4A1, AK47..."
    }
  ],
  "search_history": [
    {
      "searched_at": "2024-01-15T15:30:00Z",
      "searched_by": "admin",
      "persona_name": "PlayerName",
      "vac_bans": 0,
      "game_bans": 0,
      "changes": {}
    }
  ]
}
```

## Key Features Implemented

### 1. Search Tracking
✅ Counts how many times each Steam ID is searched
✅ Records who performed each search
✅ Tracks first and last search timestamps
✅ Maintains detailed history of all searches

### 2. Change Detection
✅ Detects persona name changes
✅ Identifies new VAC/game bans
✅ Notices profile visibility changes
✅ Stores changes in JSON format
✅ Highlights changes in UI

### 3. Ban Information
✅ VAC bans from Steam API
✅ Game bans from Steam API
✅ Days since last ban
✅ Community ban status
✅ Trade restriction status
✅ Visual indicators and warnings

### 4. Related Templates
✅ Links Steam profiles to refund requests
✅ Shows all historical refund requests for a Steam ID
✅ Displays ticket status and details
✅ Quick access from profile view

### 5. Data from Multiple Sources
✅ Steam Web API - Player Summaries
✅ Steam Web API - Player Bans
✅ Account creation date
✅ Profile level (when available)
✅ Real name and location (if public)

### 6. UI Enhancements
✅ Comprehensive profile modal
✅ Color-coded ban indicators
✅ Change alerts with old/new values
✅ Search history timeline
✅ Related templates list
✅ Responsive design
✅ Dark theme integration

## Usage Examples

### Backend
```python
from apps.templates_manager.services import SteamLookupService

# Lookup a profile
service = SteamLookupService()
result = service.lookup_profile('STEAM_0:1:12345678', user=request.user)

# Access data
print(f"Name: {result['profile']['name']}")
print(f"VAC Bans: {result['bans']['vac_bans']}")
print(f"Total Searches: {result['search_stats']['total_searches']}")
print(f"Related Templates: {len(result['related_templates'])}")
```

### Frontend
```typescript
// Lookup profile
const response = await templateAPI.steamLookup('76561197984856085');
const profile = response.data;

// Display enhanced profile
<EnhancedSteamProfile 
  profile={profile}
  onClose={() => setShowProfileModal(false)}
/>
```

## Testing Checklist

- [ ] Test Steam ID format conversions (Steam64, STEAM_X:Y:Z, [U:1:XXXXX])
- [ ] Verify ban data fetching from Steam API
- [ ] Test search count incrementing
- [ ] Verify change detection (rename account, add ban, change privacy)
- [ ] Test related templates linking
- [ ] Verify search history recording
- [ ] Test modal open/close functionality
- [ ] Verify responsive design on mobile
- [ ] Test with private profiles
- [ ] Test with limited accounts
- [ ] Test with VAC banned accounts
- [ ] Test with profiles that have no data

## Admin Tasks

To view and manage Steam profile data:
1. Go to Django Admin: `/admin/`
2. Navigate to "Templates Manager" → "Steam Profile Searches"
3. View search statistics, ban information, and history
4. Filter by bans, privacy settings
5. Search by Steam ID or name

## Future Enhancements

Potential additions:
- Export search history to CSV
- Advanced analytics (most searched, ban trends)
- Automated ban alerts for staff
- Integration with game server logs
- Steam group membership tracking
- Friend list analysis (if public)
- Game playtime statistics
- Inventory value estimation
- Automated refund approval based on clean record

## Dependencies

### Backend
- Django 4.2+
- Django REST Framework
- requests (for Steam API calls)
- Existing: python-a2s (for game servers)

### Frontend
- date-fns (for date formatting)
- @heroicons/react (icons)
- Existing: React, Next.js, TailwindCSS

## Performance Considerations

- Search records are indexed on `steam_id_64`
- History queries limited to 50 most recent
- Related templates limited to 10 most recent
- API calls to Steam have 10-second timeout
- Results are cached in database (no redundant API calls unless refresh)

## Security Notes

- Steam API key stored in environment variables
- User authentication required for all endpoints
- Search tracking includes user identification
- Admin-only access to search statistics views
- No sensitive data exposed to unauthorized users

## Migration Notes

The migration is backward compatible:
- Existing `RefundTemplate` records are not affected
- `steam_profile` field is nullable
- No data loss during migration
- Can be rolled back safely if needed

## Testing the Implementation

1. **Backend Test**:
```bash
cd backend
python manage.py shell

from apps.templates_manager.services import SteamLookupService
from apps.accounts.models import CustomUser

user = CustomUser.objects.first()
service = SteamLookupService()
result = service.lookup_profile('76561197984856085', user=user)
print(result)
```

2. **Frontend Test**:
- Navigate to `/dashboard/templates`
- Enter a Steam ID in the lookup field
- Click "Lookup"
- View the inline summary
- Click "View Full Profile"
- Verify all sections display correctly

## Support & Maintenance

For issues or questions:
- Check Django admin for search records
- Review Celery logs for scheduled tasks
- Monitor Steam API rate limits
- Verify environment variables are set correctly
- Check database indexes for performance
