import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import Staff, StaffRoster
from django.db import transaction

print('=== CLEANING UP INVALID STAFF RECORDS ===\n')

# Find all staff with invalid Steam IDs
invalid_staff = Staff.objects.exclude(steam_id__startswith='STEAM_0:')

print(f'Found {invalid_staff.count()} staff records with invalid Steam IDs\n')

if invalid_staff.exists():
    print('Invalid records to be deleted:')
    for staff in invalid_staff:
        print(f'  - steam_id="{staff.steam_id}", name="{staff.name}", status={staff.staff_status}')
    
    confirm = input(f'\nDelete these {invalid_staff.count()} invalid records? (yes/no): ')
    
    if confirm.lower() == 'yes':
        with transaction.atomic():
            # First, get the roster entries linked to these staff
            roster_entries = StaffRoster.objects.filter(staff__in=invalid_staff)
            roster_count = roster_entries.count()
            
            print(f'\nDeleting {roster_count} associated roster entries...')
            roster_entries.delete()
            
            print(f'Deleting {invalid_staff.count()} invalid staff records...')
            deleted_count = invalid_staff.delete()[0]
            
            print(f'\n✓ Cleanup complete!')
            print(f'  - Deleted {deleted_count} invalid Staff records')
            print(f'  - Deleted {roster_count} associated StaffRoster entries')
            
            # Show final counts
            remaining_staff = Staff.objects.count()
            print(f'\nRemaining Staff records: {remaining_staff}')
            print(f'  - Active: {Staff.objects.filter(staff_status="active").count()}')
            print(f'  - Inactive: {Staff.objects.filter(staff_status="inactive").count()}')
    else:
        print('Cleanup cancelled.')
else:
    print('No invalid records found. Database is clean!')
