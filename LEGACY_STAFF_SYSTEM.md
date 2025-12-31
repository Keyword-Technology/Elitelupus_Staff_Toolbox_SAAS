# Legacy Staff System Implementation

## Overview
When a staff member is removed from the Google Sheets staff roster, they are now automatically moved to "legacy staff" status instead of being deleted or simply marked inactive. This preserves their account and history while appropriately revoking their staff privileges.

## Key Features

### 1. **Staff Removal → Legacy Staff**
When a staff member is removed from the roster:
- **Not deleted** - Their account remains in the User table
- **Marked as legacy** - `is_legacy_staff = True`
- **Demoted to User** - Role changed to 'User' (priority 999)
- **Staff status removed** - `is_active_staff = False`
- **Timestamp recorded** - `staff_left_at` set to removal time
- **Account stays active** - `is_active = True` (can still login)
- **History preserved** - StaffHistoryEvent created with 'removed' type

### 2. **Re-adding Legacy Staff → Promotion to SYSADMIN**
When a legacy staff member is re-added to the roster:
- **Promoted to SYSADMIN** - Automatically given highest role
- **Legacy status cleared** - `is_legacy_staff = False`
- **Active staff restored** - `is_active_staff = True`
- **Timestamp cleared** - `staff_left_at = None`
- **Full privileges** - Priority set to 0 (SYSADMIN level)

## Database Changes

### User Model (apps/accounts/models.py)
New fields added:
```python
is_legacy_staff = models.BooleanField(default=False)  # Former staff not in roster
staff_left_at = models.DateTimeField(null=True, blank=True)  # When removed from roster
```

### Migration
Created: `apps/accounts/migrations/0002_user_is_legacy_staff_user_staff_left_at.py`

## Backend Changes

### Service Layer (apps/staff/services.py)

#### New Method: `_move_to_legacy_staff(roster_entry)`
Handles moving removed staff to legacy status:
- Gets or creates a User account for the staff member
- Sets legacy staff flags and timestamps
- Demotes to regular User role
- Preserves Steam/Discord identifiers for future re-linking

#### Updated Method: `_link_to_user(roster_entry)`
Now checks for legacy staff status:
- If user has `is_legacy_staff=True`, promotes to SYSADMIN
- Otherwise, updates role based on roster data
- Clears legacy flags when re-added

#### Updated Method: `sync_user_access()`
Modified to handle legacy staff:
- Moves staff not in roster to legacy instead of deactivating
- Keeps accounts active for legacy staff
- Properly tracks state transitions

#### Updated Sync Logic
In the main `sync_staff_roster()` method:
- Calls `_move_to_legacy_staff()` before marking roster entry inactive
- Creates history event with 'removed' type
- Preserves all audit trail

### API Endpoints

#### New Endpoint: Legacy Staff List
```
GET /api/auth/staff/legacy/
```
Returns all legacy staff members, ordered by when they left.

**Response Example:**
```json
[
  {
    "id": 5,
    "username": "john_doe",
    "display_name": "John Doe",
    "role": "User",
    "role_priority": 999,
    "is_active_staff": false,
    "is_legacy_staff": true,
    "staff_since": "2023-01-15T10:00:00Z",
    "staff_left_at": "2024-12-31T15:30:00Z",
    "steam_id": "STEAM_0:1:12345678",
    "discord_id": "123456789012345678"
  }
]
```

### Admin Interface (apps/accounts/admin.py)

Updated User admin to show:
- `is_legacy_staff` in list display
- `staff_left_at` in Staff Info fieldset
- Filter by legacy staff status

### Serializers (apps/accounts/serializers.py)

Updated `UserSerializer` to include:
- `is_legacy_staff` (read-only)
- `staff_left_at` (read-only)

## Workflow Examples

### Scenario 1: Staff Member Removed from Roster
```
1. Staff sync detects user "john_doe" no longer in Google Sheet
2. System calls _move_to_legacy_staff()
3. User account updated:
   - is_legacy_staff: false → true
   - is_active_staff: true → false
   - role: "Admin" → "User"
   - role_priority: 70 → 999
   - staff_left_at: null → "2024-12-31T15:30:00Z"
   - is_active: remains true
4. StaffRoster entry marked inactive
5. StaffHistoryEvent created with type 'removed'
6. User can still login but has no staff privileges
```

### Scenario 2: Legacy Staff Re-added to Roster
```
1. Staff sync finds "john_doe" back in Google Sheet
2. System detects is_legacy_staff=true in _link_to_user()
3. User account updated:
   - role: "User" → "SYSADMIN"
   - role_priority: 999 → 0
   - is_legacy_staff: true → false
   - is_active_staff: false → true
   - staff_left_at: "2024-12-31..." → null
4. StaffRoster entry created/reactivated
5. StaffHistoryEvent created with type 'rejoined'
6. User now has full SYSADMIN privileges
```

## Benefits

1. **Data Preservation**: No staff data is ever lost
2. **Account Continuity**: Users maintain access to their accounts
3. **Audit Trail**: Complete history of staff status changes
4. **Security**: Former staff have no elevated privileges
5. **Re-hiring Friendly**: Easy to restore privileges when staff return
6. **Automatic Promotion**: Re-added staff get SYSADMIN role automatically

## API Usage

### Get Legacy Staff List
```bash
curl -X GET http://localhost:8000/api/auth/staff/legacy/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Active Staff (excludes legacy)
```bash
curl -X GET http://localhost:8000/api/auth/staff/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Admin Usage

1. Navigate to Django Admin → Users
2. Filter by "Is legacy staff"
3. View `staff_left_at` timestamp for each legacy staff member
4. See complete history in StaffHistoryEvent

## Future Enhancements

Potential improvements:
- Frontend UI to display legacy staff list
- Notification system when legacy staff are re-added
- Configurable promotion role (instead of always SYSADMIN)
- Legacy staff badge/indicator in user profiles
- Statistics on staff retention and turnover
