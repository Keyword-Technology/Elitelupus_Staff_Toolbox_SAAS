import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import (ServerSession, Staff, StaffHistoryEvent,
                               StaffRoster)

print("=== Staff Table ===")
print(f"Total Staff records: {Staff.objects.count()}")
print("\nSample Staff records:")
for s in Staff.objects.all()[:10]:
    print(f"  {s.steam_id} - {s.name} ({s.staff_status})")

print("\n=== StaffRoster Table ===")
print(f"Total StaffRoster records: {StaffRoster.objects.count()}")
print("\nSample StaffRoster records (with staff_id):")
for sr in StaffRoster.objects.all()[:5]:
    print(f"  ID={sr.id}, staff_id={sr.staff_id}")

print("\n=== ServerSession Table ===")
print(f"Total ServerSession records: {ServerSession.objects.count()}")
print("\nDistinct staff_id values in ServerSession:")
staff_ids = ServerSession.objects.values_list('staff_id', flat=True).distinct()
print(f"  Found {len(staff_ids)} unique staff_id values")
print(f"  Sample staff_ids: {list(staff_ids)[:20]}")

print("\n=== Checking for Orphaned ServerSession Records ===")
# Get all staff_ids from ServerSession
session_staff_ids = set(ServerSession.objects.values_list('staff_id', flat=True))
# Get all steam_ids from Staff
staff_steam_ids = set(Staff.objects.values_list('steam_id', flat=True))

# Find staff_ids in ServerSession that don't exist in Staff
orphaned_ids = session_staff_ids - staff_steam_ids
if orphaned_ids:
    print(f"Found {len(orphaned_ids)} orphaned staff_ids in ServerSession:")
    print(f"  {sorted(orphaned_ids)[:20]}")
else:
    print("No orphaned staff_ids found!")

print("\n=== Checking if staff_id is numeric (old ID) or steam_id ===")
sample_sessions = ServerSession.objects.all()[:5]
for session in sample_sessions:
    print(f"  staff_id={session.staff_id} (type: {type(session.staff_id).__name__})")
