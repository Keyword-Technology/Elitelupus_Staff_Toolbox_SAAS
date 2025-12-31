import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.staff.models import Staff, StaffRoster
from django.db.models import Count

print('=== STAFF DATA ANALYSIS ===\n')

# Total counts
total_staff = Staff.objects.count()
active_staff = Staff.objects.filter(staff_status='active').count()
inactive_staff = Staff.objects.filter(staff_status='inactive').count()

print(f'Total Staff records: {total_staff}')
print(f'Active Staff: {active_staff}')
print(f'Inactive Staff: {inactive_staff}\n')

# User linkage
staff_with_users = Staff.objects.filter(user__isnull=False).count()
inactive_with_users = Staff.objects.filter(staff_status='inactive', user__isnull=False).count()
inactive_without_users = Staff.objects.filter(staff_status='inactive', user__isnull=True).count()

print(f'Staff with linked users: {staff_with_users}/{total_staff}')
print(f'Inactive staff WITH user: {inactive_with_users}')
print(f'Inactive staff WITHOUT user: {inactive_without_users}\n')

# Legacy staff users
legacy_users = User.objects.filter(is_legacy_staff=True).count()
print(f'Users marked as legacy staff: {legacy_users}\n')

# Check for duplicate/bad data
print('=== DATA QUALITY ISSUES ===\n')

# Staff records without proper Steam IDs
invalid_steam = Staff.objects.exclude(steam_id__startswith='STEAM_0:')
print(f'Staff with invalid Steam IDs: {invalid_steam.count()}')
if invalid_steam.exists():
    print('Sample invalid Steam IDs:')
    for s in invalid_steam[:10]:
        print(f'  - "{s.steam_id}": {s.name} ({s.staff_status})')

# Check for duplicates by name
duplicates = Staff.objects.values('name').annotate(count=Count('steam_id')).filter(count__gt=1)
print(f'\nDuplicate staff names: {duplicates.count()}')
if duplicates.exists():
    print('Sample duplicates:')
    for dup in duplicates[:5]:
        name = dup['name']
        count = dup['count']
        print(f'  - "{name}": {count} records')
        staff_with_name = Staff.objects.filter(name=name)
        for s in staff_with_name:
            print(f'      steam_id={s.steam_id}, status={s.staff_status}')

# Check roster entries
print('\n=== ROSTER DATA ===\n')
total_roster = StaffRoster.objects.count()
active_roster = StaffRoster.objects.filter(is_active=True).count()
inactive_roster = StaffRoster.objects.filter(is_active=False).count()

print(f'Total Roster entries: {total_roster}')
print(f'Active Roster: {active_roster}')
print(f'Inactive Roster: {inactive_roster}')
