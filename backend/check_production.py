import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import ServerSession, Staff
from django.utils import timezone

print("=" * 80)
print("Production Database Check")
print("=" * 80)
print(f"Current time: {timezone.now()}")
print()

# Count staff with last_seen set
staff_with_last_seen = Staff.objects.exclude(last_seen__isnull=True).count()
staff_without_last_seen = Staff.objects.filter(last_seen__isnull=True).count()
total_staff = Staff.objects.count()

print(f"Staff with last_seen set: {staff_with_last_seen}/{total_staff}")
print(f"Staff without last_seen: {staff_without_last_seen}/{total_staff}")
print()

# Show sample staff with their last_seen times
print("Sample staff members:")
print("-" * 80)
for staff in Staff.objects.filter(staff_status='active').order_by('-last_seen')[:10]:
    sessions = ServerSession.objects.filter(staff=staff).count()
    print(f"{staff.name:20} | last_seen: {staff.last_seen} | Sessions: {sessions}")
print("=" * 80)
