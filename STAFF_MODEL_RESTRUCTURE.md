# Staff Model Restructure - Implementation Guide

## Overview

This document outlines the database restructure to make `Staff` the permanent core entity instead of `StaffRoster`. This ensures staff records are never lost when removed from the Google Sheets roster.

## Current vs New Architecture

### Current (Problematic)
```
StaffRoster (from Google Sheets)
  ├── Sessions (linked to StaffRoster)
  ├── History (linked to StaffRoster)
  └── User (linked to StaffRoster)

Problem: When StaffRoster is inactive, accessing staff details gives 404
```

### New (Correct)
```
Staff (permanent, keyed by steam_id)
  ├── Sessions (linked to Staff)
  ├── History (linked to Staff)
  ├── User (linked to Staff)
  └── StaffRoster entries (current roster links to Staff)

Benefit: Staff records always exist, roster is just current status
```

## New Models

### 1. Staff Model (Core Entity)
```python
class Staff(models.Model):
    # Primary key
    steam_id = models.CharField(max_length=50, unique=True, primary_key=True)
    
    # Basic info
    name = models.CharField(max_length=100)
    discord_id = models.CharField(max_length=50, blank=True, null=True)
    discord_tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Current status
    staff_status = models.CharField(
        max_length=20,
        choices=[('active', 'Active Staff'), ('inactive', 'Inactive/Removed'), ('loa', 'Leave of Absence')],
        default='active'
    )
    
    # Current role (synced from roster)
    current_role = models.CharField(max_length=50, blank=True)
    current_role_priority = models.IntegerField(default=999)
    
    # User link
    user = models.OneToOneField(User, null=True, related_name='staff_profile')
    
    # Timestamps
    first_joined = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    staff_since = models.DateTimeField(null=True, blank=True)
    staff_left_at = models.DateTimeField(null=True, blank=True)
```

### 2. StaffRoster Model (Roster Entries)
```python
class StaffRoster(models.Model):
    # Link to permanent staff record
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, to_field='steam_id')
    
    # Roster data from Google Sheets
    rank = models.CharField(max_length=50)
    rank_priority = models.IntegerField(default=999)
    timezone = models.CharField(max_length=50, blank=True)
    active_time = models.CharField(max_length=20, blank=True)
    
    # Discord status
    discord_status = models.CharField(...)
    discord_custom_status = models.CharField(...)
    
    # Metadata
    last_synced = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # In current roster
    
    # Backwards compatibility properties
    @property
    def name(self): return self.staff.name
    @property
    def steam_id(self): return self.staff.steam_id
    @property
    def user(self): return self.staff.user
```

### 3. Related Models Updated
```python
class ServerSession(models.Model):
    staff = models.ForeignKey(Staff, to_field='steam_id')  # Now references Staff
    
class StaffHistoryEvent(models.Model):
    staff = models.ForeignKey(Staff, to_field='steam_id')  # Now references Staff
    
class ServerSessionAggregate(models.Model):
    staff = models.ForeignKey(Staff, to_field='steam_id')  # Now references Staff
```

## Migration Strategy

### Phase 1: Create Staff Table
1. Create new `Staff` model
2. Migrate existing `StaffRoster` data to `Staff`
3. Create Staff records for all unique steam_ids

### Phase 2: Update StaffRoster
1. Add `staff` ForeignKey to `StaffRoster`
2. Populate staff_id for all existing roster entries
3. Remove duplicate fields (name, steam_id, discord_id, etc.)
4. Add backwards compatibility properties

### Phase 3: Update Related Models
1. Change ServerSession.staff to reference Staff
2. Change StaffHistoryEvent.staff to reference Staff
3. Change ServerSessionAggregate.staff to reference Staff
4. Migrate existing foreign key references

### Phase 4: Update Code
1. Update serializers to work with new structure
2. Update views to query Staff instead of StaffRoster
3. Update sync service to create/update Staff records
4. Update admin interface

## Sync Process Changes

### Old Process
```python
# When syncing from Google Sheets:
1. Find or create StaffRoster entry
2. Update fields
3. Mark removed entries as inactive
```

### New Process
```python
# When syncing from Google Sheets:
1. Find or create Staff record (by steam_id)
2. Update Staff.current_role, Staff.name, etc.
3. Find or create StaffRoster entry (linked to Staff)
4. Update StaffRoster.rank, timezone, etc.
5. Mark removed StaffRoster entries as inactive
6. Update Staff.staff_status based on roster
```

## API Behavior Changes

### Staff Details Endpoint
**Old**: `/api/staff/roster/47/details/` - 404 if roster entry inactive  
**New**: `/api/staff/47/details/` - Always works (uses steam_id)

### Staff List Endpoint
**Old**: `/api/staff/roster/` - Returns StaffRoster entries  
**New**: `/api/staff/` - Returns Staff records with roster info

### Legacy Staff Endpoint
**Old**: Shows inactive StaffRoster entries  
**New**: Shows Staff with status='inactive'

## Benefits

1. **No Data Loss**: Staff records never deleted
2. **No 404s**: Staff details always accessible
3. **Better History**: Complete timeline even after removal
4. **Cleaner Architecture**: Separation of permanent data vs current roster
5. **Multiple Rosters**: Could track multiple roster entries per staff (history)
6. **Better Queries**: Direct queries on steam_id (primary key)

## Implementation Steps

1. **Backup Database**: Critical before starting
2. **Create Migration**: Manual migration with data transfer
3. **Test Migration**: On development database first
4. **Update Code**: Services, views, serializers
5. **Test Thoroughly**: Ensure all features work
6. **Deploy**: Apply migration to production

## Code Changes Required

### Services (apps/staff/services.py)
- Update `sync_staff_roster()` to create/update Staff first
- Update `_link_to_user()` to work with Staff
- Add `get_or_create_staff()` method

### Serializers (apps/staff/serializers.py)
- Create `StaffSerializer` for Staff model
- Update `StaffRosterSerializer` to include staff data
- Update `StaffDetailsSerializer` to use Staff

### Views (apps/staff/views.py)
- Create `StaffListView` and `StaffDetailView`
- Update existing views to use Staff where appropriate
- Maintain backwards compatibility

### Admin (apps/staff/admin.py)
- Add `StaffAdmin` for managing Staff records
- Update `StaffRosterAdmin` for roster entries

## Backwards Compatibility

The properties on StaffRoster ensure existing code continues to work:
- `roster.name` → `roster.staff.name`
- `roster.steam_id` → `roster.staff.steam_id`
- `roster.user` → `roster.staff.user`

This allows gradual migration of codebase.

## Testing Checklist

- [ ] Staff details page works for active staff
- [ ] Staff details page works for inactive staff
- [ ] Legacy staff list shows all inactive staff
- [ ] Server sessions link correctly
- [ ] Staff history events display correctly
- [ ] Sync from Google Sheets creates Staff records
- [ ] Sync updates existing Staff records
- [ ] Removing from roster marks Staff as inactive
- [ ] Re-adding to roster reactivates Staff
- [ ] User accounts link to Staff correctly

## Rollback Plan

If issues occur:
1. Keep old tables (don't drop)
2. Restore from backup
3. Review migration logs
4. Fix issues and retry

## Timeline Estimate

- Database design: 1 hour ✅ (Complete)
- Migration creation: 2 hours
- Code updates: 3-4 hours
- Testing: 2-3 hours
- **Total**: ~8-10 hours

## Status

**Current**: Models updated, needs migration creation and code updates
**Next**: Create data migration script
