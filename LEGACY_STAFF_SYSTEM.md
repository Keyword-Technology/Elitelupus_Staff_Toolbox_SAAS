# Legacy Staff System Implementation

## Overview
When a staff member is removed from the Google Sheets staff roster, their **StaffRoster entry is preserved** (marked as `is_active=False`) instead of being deleted. This maintains complete history, audit trails, and all associated data (promotions, actions, server sessions, etc.). The linked User account is also flagged as legacy staff for future reference.

## Key Features

### 1. **Staff Removal → Inactive StaffRoster Entry**
When a staff member is removed from the roster:
- **StaffRoster entry preserved** - Marked `is_active = False` (never deleted)
- **User account updated** - `is_legacy_staff = True`, `is_active_staff = False`
- **Timestamp recorded** - `staff_left_at` set to removal time
- **Account stays active** - User can still login (but no staff privileges)
- **History preserved** - All StaffHistoryEvents, ServerSessions, and actions remain linked
- **Audit trail** - StaffHistoryEvent created with 'removed' (displayed as "Demoted")

### 2. **Re-adding to Roster**
When a staff member is re-added to the roster:
- **Existing StaffRoster reactivated** - `is_active = True` (if entry exists)
- **New entry created** - If no previous entry exists
- **Promotes to SYSADMIN** - If user has `is_legacy_staff = True`
- **Updates role otherwise** - Sets role to match roster entry
- **Legacy status cleared** - `is_legacy_staff = False`, `staff_left_at = None`
- **History event** - "Rejoined Staff" event created (if previously inactive)

## Database Schema

### StaffRoster Model
```python
class StaffRoster(models.Model):
    # ... other fields ...
    is_active = models.BooleanField(default=True)  # False when removed from sheet
    user = models.OneToOneField(User, null=True)   # Link to user account
```

### User Model  
```python
class User(AbstractUser):
    is_active_staff = models.BooleanField(default=False)      # Currently active staff
    is_legacy_staff = models.BooleanField(default=False)      # Former staff (removed)
    staff_left_at = models.DateTimeField(null=True)          # When removed from roster
```

## Backend Logic

### Sync Process (apps/staff/services.py)

#### Staff Removal Handler
```python
# When staff removed from Google Sheet:
for entry in StaffRoster.objects.filter(is_active=True):
    if identifier in removed_identifiers:
        # 1. Mark roster entry inactive (preserves all data)
        entry.is_active = False
        entry.save()
        
        # 2. Update linked user account
        if entry.user:
            entry.user.is_active_staff = False
            entry.user.is_legacy_staff = True
            entry.user.staff_left_at = timezone.now()
            entry.user.save()
        
        # 3. Create history event
        StaffHistoryEvent.objects.create(
            staff=entry,              # Linked to StaffRoster (preserved!)
            event_type='removed',
            old_rank=entry.rank,
            ...
        )
```

#### Staff Re-addition Handler
```python
def _link_to_user(self, roster_entry):
    # Find existing user by Steam ID or Discord ID
    user = User.objects.filter(steam_id=roster_entry.steam_id).first()
    
    if user and user.is_legacy_staff:
        # Returning legacy staff - promote to SYSADMIN
        user.role = 'SYSADMIN'
        user.role_priority = 0
        user.is_active_staff = True
        user.is_legacy_staff = False
        user.staff_left_at = None
        user.save()
    elif user:
        # Regular update - match roster role
        user.role = roster_entry.rank
        user.is_active_staff = True
        user.save()
```

## API Endpoints

### Active Staff
```
GET /api/staff/roster/
```
Returns only active staff (`is_active=True`)

### Inactive/Legacy Staff
```
GET /api/staff/roster/?show_inactive=true
```
Returns all staff (both active and inactive)

**Frontend filtering:**
```typescript
const inactiveStaff = response.data.filter((s: StaffMember) => !s.is_active);
```

### User Legacy Staff List
```
GET /api/auth/staff/legacy/
```
Returns User accounts with `is_legacy_staff=True`

## Workflow Examples

### Scenario 1: Staff Member Removed
```
1. John Doe removed from Google Sheet
2. Sync detects identifier missing
3. StaffRoster entry updated:
   - is_active: true → false
   - (all other data preserved: rank, history, sessions, etc.)
4. User account updated:
   - is_active_staff: true → false
   - is_legacy_staff: false → true
   - staff_left_at: null → "2024-12-31T15:30:00Z"
5. StaffHistoryEvent created:
   - event_type: 'removed' (displays as "Demoted")
   - staff: links to preserved StaffRoster entry
6. User can still login but has no staff privileges
7. All historical data remains: promotions, actions, server time, etc.
```

### Scenario 2: Legacy Staff Re-added
```
1. John Doe added back to Google Sheet
2. Sync finds existing inactive StaffRoster entry (by Steam/Discord ID)
3. StaffRoster entry reactivated:
   - is_active: false → true
   - rank: updated to match sheet
4. User detected as is_legacy_staff=true
5. User account updated:
   - role: "User" → "SYSADMIN"
   - role_priority: 999 → 0
   - is_active_staff: false → true
   - is_legacy_staff: true → false
   - staff_left_at: "2024..." → null
6. StaffHistoryEvent created:
   - event_type: 'rejoined'
7. User now has SYSADMIN privileges
8. All historical data still linked (never lost!)
```

### Scenario 3: New Staff Member
```
1. New person added to Google Sheet
2. New StaffRoster entry created:
   - All fields populated from sheet
   - is_active: true
3. Attempts to link to User account (by Steam/Discord ID)
4. If User found: links and updates role
5. If no User: entry created without user link
6. StaffHistoryEvent created:
   - event_type: 'joined'
```

## Data Preservation

### What's Preserved When Staff Removed:
✅ **StaffRoster entry** - All fields intact, just marked inactive  
✅ **User account** - Still exists, can login, marked legacy  
✅ **StaffHistoryEvents** - All historical events (joined, promoted, demoted, etc.)  
✅ **ServerSessions** - All game server sessions via foreign key to StaffRoster  
✅ **Counter history** - All sit/ticket counter data (if linked to User)  
✅ **Audit trail** - Complete timeline of staff member's career

### What Changes:
- `StaffRoster.is_active`: `true` → `false`
- `User.is_active_staff`: `true` → `false`  
- `User.is_legacy_staff`: `false` → `true`
- `User.staff_left_at`: `null` → timestamp

### What's NOT Changed:
- All foreign key relationships intact
- Historical data preserved
- User can still login
- No data deletion occurs

## Benefits

1. **Complete History**: Never lose staff member data
2. **Audit Compliance**: Full timeline of all staff changes
3. **Data Integrity**: Foreign keys remain valid (StaffRoster never deleted)
4. **Easy Re-hiring**: Automatic SYSADMIN promotion for returning staff
5. **Analytics**: Can track staff retention, turnover, and patterns
6. **Investigation Support**: Historical server sessions and actions preserved

## Frontend Integration

The frontend already correctly handles inactive staff:

```typescript
// View legacy staff
const fetchLegacyStaff = async () => {
  const response = await staffAPI.roster('?show_inactive=true&ordering=rank_priority');
  const inactiveStaff = response.data.filter((s: StaffMember) => !s.is_active);
  setStaff(inactiveStaff);
};
```

**Page:** `/dashboard/staff/legacy`  
**Shows:** All inactive StaffRoster entries with complete history

## Admin Usage

1. Navigate to Django Admin → Staff Roster
2. Filter by "Is active" = No
3. View complete inactive staff list
4. Click any entry to see full history and data
5. All StaffHistoryEvents visible (even for inactive staff)

## Migration Applied

**Migration:** `apps/accounts/migrations/0002_user_is_legacy_staff_user_staff_left_at.py`

Added fields:
- `User.is_legacy_staff` (BooleanField, default=False)
- `User.staff_left_at` (DateTimeField, null=True)

## Future Enhancements

- Restore specific role instead of always SYSADMIN
- Legacy staff statistics dashboard
- Notification when legacy staff return
- Export legacy staff reports
- Legacy staff badge/indicator in profiles
