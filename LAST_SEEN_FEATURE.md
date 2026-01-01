# Last Seen Feature Implementation

## Overview
Added a "Last Seen" feature to the staff roster that shows how long ago each staff member was last seen on the game servers.

## Changes Made

### Backend Changes

#### 1. `apps/servers/services.py`
- **Modified `_track_session_changes` method**: Now updates the `Staff.last_seen` timestamp when a staff member leaves a server
- When a staff member disconnects, the system records the current timestamp to track when they were last online
- This ensures we always have an accurate record of the last time they were on a server

#### 2. `apps/staff/serializers.py`
- **Added `last_seen_ago` field** to `StaffRosterSerializer`
- **Implemented `get_last_seen_ago` method**: Calculates human-readable time differences
  - If currently online: Returns `None` (UI shows "Online")
  - If never seen: Returns `"Never"`
  - Otherwise calculates time difference and returns:
    - "Just now" (< 1 minute)
    - "X minutes ago" (< 1 hour)
    - "X hours ago" (< 1 day)
    - "X days ago" (< 1 week)
    - "X weeks ago" (< 1 month)
    - "X months ago" (< 1 year)
    - "X years ago" (>= 1 year)

### Frontend Changes

#### 1. `frontend/src/app/dashboard/staff/page.tsx`
- **Updated `StaffMember` interface**: Added `last_seen_ago?: string | null` field
- **Modified table header**: Changed "Online" column to "Last Seen" with WifiIcon
- **Updated table cell rendering**: 
  - If online: Shows green indicator with "Online" and server name
  - If has last_seen_ago: Shows gray indicator with time ago text
  - If never seen: Shows dark gray indicator with "Never"

## Database Migrations
- Applied migration `staff.0010_alter_staffroster_options_alter_serversession_staff_and_more`
- Applied migration `system_settings.0003_alter_systemsetting_category`

## Testing
Created `backend/test_last_seen.py` to verify the time calculation logic works correctly for various time intervals:
- ✅ Just now (< 1 minute)
- ✅ 5 minutes ago
- ✅ 2 hours ago
- ✅ 12 hours ago  
- ✅ 3 days ago
- ✅ 2 weeks ago
- ✅ 2 months ago

All tests passed successfully!

## User Experience
- Staff members who are currently online show as "Online" with their current server
- Staff members who are offline show how long ago they were last seen (e.g., "2 hours ago")
- Staff members who have never been seen show "Never"
- The information updates in real-time as staff join/leave servers
- The UI uses color coding: green for online, gray for offline

## Technical Details
- The `Staff.last_seen` field is updated automatically by the server query service
- Time calculations are done server-side for consistency across timezones
- The serializer checks ServerPlayer records to determine current online status
- The frontend displays the pre-calculated time ago string from the API
- All time differences are calculated relative to `timezone.now()` for accuracy

## Future Enhancements
- Could add sorting by last_seen_ago in the staff roster
- Could add filtering to show only staff seen within a certain timeframe
- Could add a tooltip showing the exact timestamp of last seen
- Could track last seen per server for more detailed history
