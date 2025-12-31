import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import Staff, StaffRoster
from apps.staff.services import StaffSyncService

print("=" * 80)
print("TESTING STAFF SYNC SERVICE WITH NEW STRUCTURE")
print("=" * 80)

# Test sync service initialization
service = StaffSyncService()

print("\n1. Service Initialization:")
print(f"   Sheet ID: {service.sheet_id}")
print(f"   Sheet URL: {service.sheet_url}")

print("\n2. Pre-sync State:")
print(f"   Staff count: {Staff.objects.count()}")
print(f"   Active roster: {StaffRoster.objects.filter(is_active=True).count()}")
print(f"   Inactive roster: {StaffRoster.objects.filter(is_active=False).count()}")

# Try running sync
print("\n3. Running Staff Sync...")
try:
    log = service.sync_staff_roster()
    print(f"   ✓ Sync completed successfully!")
    print(f"   Records synced: {log.records_synced}")
    print(f"   Records added: {log.records_added}")
    print(f"   Records updated: {log.records_updated}")
    print(f"   Records removed: {log.records_removed}")
except Exception as e:
    print(f"   ✗ Sync failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Post-sync State:")
print(f"   Staff count: {Staff.objects.count()}")
print(f"   Active roster: {StaffRoster.objects.filter(is_active=True).count()}")
print(f"   Inactive roster: {StaffRoster.objects.filter(is_active=False).count()}")

print("\n5. Sample Active Staff:")
for roster in StaffRoster.objects.filter(is_active=True).select_related('staff')[:5]:
    print(f"   - {roster.staff.name} ({roster.rank}) [{roster.staff.steam_id}]")

print("\n" + "=" * 80)
print("SYNC TEST COMPLETE!")
print("=" * 80)
