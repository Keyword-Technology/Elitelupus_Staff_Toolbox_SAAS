import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import StaffRoster
from apps.staff.serializers import StaffRosterSerializer

print("Testing API Response for Staff Roster")
print("=" * 80)

# Get first 10 active staff
rosters = StaffRoster.objects.filter(is_active=True).select_related('staff')[:10]

for roster in rosters:
    serializer = StaffRosterSerializer(roster)
    data = serializer.data
    
    last_seen = roster.staff.last_seen
    last_seen_ago = data.get('last_seen_ago')
    
    print(f"{roster.staff.name:20} | DB last_seen: {last_seen} | API returns: {last_seen_ago}")

print("=" * 80)
print("\nIf all show 'Never' for staff without sessions, the API is correct.")
print("The issue is frontend caching - clear browser cache and reload.")
