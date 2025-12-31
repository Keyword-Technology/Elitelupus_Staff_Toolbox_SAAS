# Staff Roster Sync Fix - Summary

## Problem
The staff roster page was showing "0 staff members" even though there are 34 staff members in the Google Sheet.

## Root Cause
The CSV parsing logic had incorrect column indices. The Google Sheet CSV export includes an empty first column, so the actual data columns are shifted by one position:

**Actual CSV structure:**
- Column 0: Empty
- Column 1: Staff Rank  
- Column 2: Timezone
- Column 3: Time
- Column 4: Name
- Column 5: SteamID
- Column 6: Discord ID
- Column 7: Discord Tag

**Previous code was reading:**
- Column 0 as Rank (incorrect - was empty)
- Column 1 as Timezone
- Column 2 as Time
- ... etc

This caused all rows to be skipped because `row[0].strip()` was always empty.

## Changes Made

### 1. Fixed CSV Parsing (`backend/apps/staff/services.py`)
- Updated column indices to start from column 1 instead of 0
- Changed validation to check `row[1]` (Rank) instead of `row[0]`
- Added debug logging to track parsing progress
- Added 'staff rank' to the skip list for header rows

### 2. Improved Sync Logic (`backend/apps/staff/services.py`)
- Changed from Steam ID-only matching to multi-field matching
- Now supports staff members without Steam IDs
- Uses priority matching: Steam ID → Discord ID → Name
- Better handling of create vs update operations

### 3. Fixed API Response Format (`backend/apps/staff/serializers.py`)
- Added field mappings to match frontend expectations:
  - `rank` → `role`
  - `name` → `username` and `display_name`
  - `rank_color` → `role_color`
  - `rank_priority` → `role_priority`
- Added placeholder fields for LOA tracking (to be implemented later)
- Added `joined_date` and `last_activity` fallbacks

## Testing Performed

✓ Verified CSV fetch works (3372 characters retrieved)
✓ Confirmed 34 staff members in Google Sheet
✓ Tested CSV parsing - successfully parses all 34 records
✓ Sample records validated:
  - Harry (Manager) - STEAM_0:0:173485831
  - Lethal (Manager) - STEAM_0:1:432543714
  - MysticDark (Staff Manager) - STEAM_0:1:211355013
  - (and 31 more...)

## How to Test the Fix

### Option 1: Through the Web UI (Recommended)
1. Make sure the backend server is running
2. Login to the staff roster page at `/dashboard/staff`
3. Click the "Sync Now" button
4. Page should now show 34 staff members instead of 0

### Option 2: Through API
```bash
# Get auth token first (login)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Trigger sync (use token from login response)
curl -X POST http://localhost:8000/api/staff/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Check roster
curl -X GET http://localhost:8000/api/staff/roster/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Option 3: Django Management Command (Future Enhancement)
Consider adding a management command for easier testing:
```python
# backend/apps/staff/management/commands/sync_staff.py
from django.core.management.base import BaseCommand
from apps.staff.services import StaffSyncService

class Command(BaseCommand):
    help = 'Sync staff roster from Google Sheets'

    def handle(self, *args, **options):
        service = StaffSyncService()
        log = service.sync_staff_roster()
        self.stdout.write(self.style.SUCCESS(
            f'Synced {log.records_synced} records '
            f'({log.records_added} added, {log.records_updated} updated)'
        ))
```

## Expected Results After Fix

- Staff roster page should show "34 staff members" instead of "0"
- Clicking sync should show success message
- Staff table should display all 34 staff members with:
  - Names
  - Roles (Manager, Staff Manager, Admin, etc.)
  - Steam IDs
  - Discord tags
  - Role colors
- Sync log should show: "34 records synced"

## Files Modified

1. `backend/apps/staff/services.py` - CSV parsing and sync logic
2. `backend/apps/staff/serializers.py` - API response format
3. Created test files:
   - `test_csv_parse.py` - Standalone CSV parsing test
   - `test_sync.py` - Full sync test with Django

## Next Steps (Optional Improvements)

1. **Add LOA (Leave of Absence) tracking**
   - Add fields to StaffRoster model: `is_on_loa`, `loa_start`, `loa_end`
   - Update sync logic to parse LOA data if added to Google Sheet

2. **Add proper joined_date field**
   - Add to model and track when staff members join
   - Update during sync or user registration

3. **Add activity tracking**
   - Track last_activity based on counter updates or server presence
   - Show in roster table

4. **Add management command**
   - For easier testing and cron job scheduling
   - Better error output

5. **Add Celery periodic task**
   - Auto-sync every hour or daily
   - Configured in `backend/apps/staff/tasks.py`

## Notes

- The fix maintains backward compatibility
- Existing database records will be updated correctly on next sync
- No database migrations needed (only code changes)
- Auto-reload should pick up changes if dev server is running
