import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import Staff, StaffRoster
from apps.staff.serializers import StaffRosterSerializer
from django.utils import timezone
from datetime import timedelta

# Get a staff member
staff = Staff.objects.first()
if not staff:
    print("No staff members in database")
    exit()

print(f"Testing with staff: {staff.name}")
roster = StaffRoster.objects.filter(staff=staff).first()

if not roster:
    print("No roster entry found")
    exit()

# Test different time intervals
tests = [
    (timedelta(seconds=30), 'Just now'),
    (timedelta(minutes=5), '5 minutes ago'),
    (timedelta(hours=2), '2 hours ago'),
    (timedelta(hours=12), '12 hours ago'),
    (timedelta(days=3), '3 days ago'),
    (timedelta(days=14), '2 weeks ago'),
    (timedelta(days=60), '2 months ago'),
]

print("\nTesting last_seen_ago field:")
print("-" * 50)

for delta, expected in tests:
    staff.last_seen = timezone.now() - delta
    staff.save()
    
    # Re-fetch to ensure fresh data
    staff = Staff.objects.get(steam_id=staff.steam_id)
    roster = StaffRoster.objects.get(staff=staff)
    
    serializer = StaffRosterSerializer(roster)
    result = serializer.data.get('last_seen_ago')
    
    # Debug info
    now = timezone.now()
    diff = now - staff.last_seen
    print(f"Delta: {delta} | Diff: {diff} | Expected: {expected:20} | Got: {result}")

print("-" * 50)
print("\nTest complete!")
