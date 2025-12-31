import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import Staff, StaffRoster
from apps.staff.services import StaffSyncService

print("=" * 60)
print("TESTING STAFF SYNC")
print("=" * 60)

# Get current counts before sync
before_staff = Staff.objects.count()
before_roster = StaffRoster.objects.filter(is_active=True).count()
print(f"\nBefore sync:")
print(f"  Total Staff: {before_staff}")
print(f"  Active Roster: {before_roster}")

# Run sync
print("\n" + "=" * 60)
print("RUNNING SYNC...")
print("=" * 60)
service = StaffSyncService()
result = service.sync_staff_roster()

# Get counts after sync
after_staff = Staff.objects.count()
after_roster = StaffRoster.objects.filter(is_active=True).count()

print("\n" + "=" * 60)
print("SYNC RESULTS")
print("=" * 60)
print(f"After sync:")
print(f"  Total Staff: {after_staff}")
print(f"  Active Roster: {after_roster}")
print(f"\nChanges:")
print(f"  Staff added: {after_staff - before_staff}")
print(f"  Roster entries: {after_roster}")

# List all active staff
print("\n" + "=" * 60)
print("ACTIVE STAFF ROSTER")
print("=" * 60)
roster = StaffRoster.objects.filter(is_active=True).select_related('staff').order_by('rank_priority', 'staff__name')
for i, entry in enumerate(roster, 1):
    print(f"{i:2}. {entry.staff.name:20} - {entry.rank:20} ({entry.staff.steam_id})")

print(f"\n✓ Total active staff members: {roster.count()}")
if roster.count() >= 24:
    print("✓ SUCCESS: Got 24+ staff members!")
else:
    print(f"⚠ WARNING: Expected 24+ staff members, got {roster.count()}")
