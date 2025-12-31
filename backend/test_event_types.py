import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.models import StaffHistoryEvent
from django.db.models import Count

# Check all event types
print("Event type display labels:")
print("-" * 60)
for code, label in StaffHistoryEvent.EVENT_TYPES:
    count = StaffHistoryEvent.objects.filter(event_type=code).count()
    print(f"  {code:15} -> {label:20} ({count} events)")

print("\nRecent 'removed' events:")
print("-" * 60)
removed = StaffHistoryEvent.objects.filter(event_type='removed').order_by('-event_date')[:5]
for event in removed:
    print(f"  {event.staff.name:20} - {event.get_event_type_display():15} on {event.event_date.strftime('%Y-%m-%d %H:%M')}")
    if event.old_rank:
        print(f"    Was: {event.old_rank}")

if not removed:
    print("  No removed events found yet")

print("\nRecent 'demoted' events:")
print("-" * 60)
demoted = StaffHistoryEvent.objects.filter(event_type='demoted').order_by('-event_date')[:5]
for event in demoted:
    print(f"  {event.staff.name:20} - {event.get_event_type_display():15} on {event.event_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"    {event.old_rank} (priority {event.old_rank_priority}) -> {event.new_rank} (priority {event.new_rank_priority})")

if not demoted:
    print("  No demotion events found yet")
