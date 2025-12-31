# Flexible Staff Name Matching

## Overview
The system now uses flexible name matching to detect staff members on game servers, even when they have numbers at the start or end of their in-game names.

## How It Works

### Name Normalization
Staff names are normalized by removing numbers from the beginning and end of the name for matching purposes:

- `Cloudyman2` → `cloudyman` (matches roster entry "Cloudyman")
- `2Admin` → `admin` (matches roster entry "Admin")
- `Player123` → `player` (matches roster entry "Player")
- `123Staff456` → `staff` (matches roster entry "Staff")

### Matching Process
1. **Exact Match First** (fastest): Direct lowercase comparison
   - `Cloudyman` matches `Cloudyman` in roster
   
2. **Normalized Match** (fallback): Remove numbers and compare
   - `Cloudyman2` normalizes to `cloudyman`, matches `Cloudyman` in roster
   - `2Cloudyman` normalizes to `cloudyman`, matches `Cloudyman` in roster

### Implementation Details

#### Location
The matching logic is implemented in:
- `backend/apps/servers/services.py`:
  - `normalize_name(name)` - Removes numbers from start/end
  - `find_matching_staff(player_name, staff_roster_dict)` - Matches players to staff

#### Applied In
1. **Server Status Updates** (`_update_server_players`)
   - Detects which players are staff members
   - Creates ServerPlayer records with staff flags
   - Tracks staff sessions (join/leave times)

2. **Staff Distribution** (`get_staff_distribution`)
   - Shows which staff are on which servers
   - Handles staff with numbered variations

3. **Player Lookup** (`PlayerLookupView`)
   - Searches for players across servers
   - Supports fuzzy name matching

## Examples

### Scenario 1: Cloudyman's In-Game Name
**Roster Name**: `Cloudyman`  
**In-Game Variations**:
- `Cloudyman` ✓ (exact match)
- `Cloudyman2` ✓ (normalized match)
- `2Cloudyman` ✓ (normalized match)
- `CLOUDYMAN` ✓ (case-insensitive)
- `cloudyman123` ✓ (normalized match)

### Scenario 2: Regular Player
**In-Game Name**: `RandomPlayer42`  
**Result**: Not matched (no roster entry for "RandomPlayer")

## Testing

### Test Script
Run the test script to verify matching logic:
```bash
cd backend
python test_name_matching.py
```

### Management Command
Test live server queries with staff detection:
```bash
cd backend
python manage.py test_server_query
```

Example output:
```
Querying: Elitelupus US #1
  ✓ Server is online
  Staff Online (2):
    ✓ Cloudyman2 (Snr Admin) - 13m
    ✓ ofcWilliam (Moderator) - 56m
```

## Benefits

1. **Flexible Identification**: Staff can use numbered variations without losing tracking
2. **Session Tracking**: Sessions are properly linked even with name variations
3. **Accurate Statistics**: Counter and activity stats remain accurate
4. **No Configuration Needed**: Works automatically for all staff members

## Limitations

1. **Numbers in Middle**: Names like `Admin99Player` won't match `Admin` or `Player` (only removes from start/end)
2. **Special Characters**: Only handles numbers, not other special characters
3. **Similar Names**: If two staff have similar base names (e.g., "Admin" and "Admin1" as roster entries), matching priority is:
   - Exact match first
   - First normalized match found

## Database Impact

No database changes required. The matching happens at query time when comparing server player names to the staff roster.

## Future Enhancements

Potential improvements:
- [ ] Support for special character variations
- [ ] Fuzzy matching for typos (Levenshtein distance)
- [ ] Staff alias system for known variations
- [ ] Regex pattern matching for complex cases
