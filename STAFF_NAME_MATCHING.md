# Flexible Staff Name Matching

## Overview
The system now uses flexible name matching to detect staff members on game servers, even when they have numbers at the start or end of their in-game names.

## How It Works

### Two-Stage Process

The system uses a two-stage approach for accurate staff detection:

1. **Stage 1: Initial Matching** (Server Query)
   - When players are detected on server, their names are matched to staff roster
   - Uses flexible name normalization (removes numbers from start/end)
   - Matched staff get their steam_id assigned to ServerPlayer record

2. **Stage 2: Status Lookup** (Staff Roster API)
   - Staff roster page queries by steam_id (not name)
   - This ensures reliable detection regardless of name variations
   - Works even if in-game name differs from roster name

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
   - Creates ServerPlayer records with staff flags and steam_id
   - Tracks staff sessions (join/leave times)

2. **Staff Distribution** (`get_staff_distribution`)
   - Shows which staff are on which servers
   - Handles staff with numbered variations

3. **Player Lookup** (`PlayerLookupView`)
   - Searches for players across servers
   - Supports fuzzy name matching

4. **Staff Roster API** (`StaffRosterSerializer`)
   - Uses steam_id for reliable online status detection
   - Works regardless of in-game name variations
   - Shows correct server info in roster page

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

### Complete Flow Test
Test the entire flow from name matching to API serialization:
```bash
cd backend
python test_complete_flow.py
```

This test demonstrates:
- Name normalization with various inputs
- Staff matching with numbered names
- ServerPlayer creation with correct steam_id
- Staff roster API returning correct online status

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

No database changes required. The matching happens at query time when comparing server player names to the staff roster. The key is that:

1. **ServerPlayer records store the original in-game name** (e.g., "Cloudyman2")
2. **ServerPlayer records also store the matched steam_id** (e.g., "STEAM_0:0:159805824")
3. **Staff roster lookups use steam_id** for reliable cross-referencing

This architecture ensures that staff can be tracked accurately regardless of their in-game name variations, as long as they're linked via steam_id.

## Future Enhancements

Potential improvements:
- [ ] Support for special character variations
- [ ] Fuzzy matching for typos (Levenshtein distance)
- [ ] Staff alias system for known variations
- [ ] Regex pattern matching for complex cases
