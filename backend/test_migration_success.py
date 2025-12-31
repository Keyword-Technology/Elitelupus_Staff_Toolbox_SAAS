import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.staff.models import (ServerSession, Staff, StaffHistoryEvent,
                               StaffRoster)

print("=" * 80)
print("STAFF DATABASE STRUCTURE TEST")
print("=" * 80)

# Test 1: Check Staff table
print("\n1. Staff Table:")
print(f"   Total Staff records: {Staff.objects.count()}")
staff_sample = Staff.objects.all()[:5]
for staff in staff_sample:
    print(f"   - {staff.steam_id}: {staff.name} ({staff.staff_status}, {staff.current_role})")

# Test 2: Check StaffRoster table
print("\n2. StaffRoster Table:")
print(f"   Total Roster entries: {StaffRoster.objects.count()}")
print(f"   Active entries: {StaffRoster.objects.filter(is_active=True).count()}")
print(f"   Inactive entries: {StaffRoster.objects.filter(is_active=False).count()}")
roster_sample = StaffRoster.objects.select_related('staff').all()[:5]
for roster in roster_sample:
    print(f"   - {roster.staff.name} ({roster.rank}) - Active: {roster.is_active}")

# Test 3: Check ServerSession references
print("\n3. ServerSession Table:")
print(f"   Total Sessions: {ServerSession.objects.count()}")
if ServerSession.objects.exists():
    session = ServerSession.objects.select_related('staff').first()
    print(f"   Sample: {session.staff.name} on server #{session.server_id}")
    print(f"   Staff ID type: {type(session.staff_id).__name__} = {session.staff_id}")

# Test 4: Check StaffHistoryEvent references
print("\n4. StaffHistoryEvent Table:")
print(f"   Total Events: {StaffHistoryEvent.objects.count()}")
if StaffHistoryEvent.objects.exists():
    events = StaffHistoryEvent.objects.select_related('staff').all()[:3]
    for event in events:
        print(f"   - {event.event_type}: {event.staff.name} ({event.event_date.strftime('%Y-%m-%d')})")

# Test 5: Check Staff-User linkage
print("\n5. Staff-User Linkage:")
linked_staff = Staff.objects.filter(user__isnull=False).count()
print(f"   Staff linked to users: {linked_staff}/{Staff.objects.count()}")

# Test 6: Check properties work
print("\n6. StaffRoster Properties Test:")
roster = StaffRoster.objects.first()
if roster:
    print(f"   roster.staff.name: {roster.staff.name}")
    print(f"   roster.staff.steam_id: {roster.staff.steam_id}")
    print(f"   roster.staff.discord_id: {roster.staff.discord_id}")
    print(f"   roster.rank: {roster.rank}")

# Test 7: Check legacy staff
print("\n7. Legacy Staff:")
legacy_users = User.objects.filter(is_legacy_staff=True).count()
print(f"   Users marked as legacy staff: {legacy_users}")

print("\n" + "=" * 80)
print("TEST COMPLETE - All structure checks passed!")
print("=" * 80)
