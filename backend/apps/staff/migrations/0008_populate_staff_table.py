# Migration to populate Staff table from existing StaffRoster data

from django.db import migrations
from django.utils import timezone


def populate_staff_from_roster(apps, schema_editor):
    """Create Staff records from existing StaffRoster entries."""
    StaffRoster = apps.get_model('staff', 'StaffRoster')
    Staff = apps.get_model('staff', 'Staff')
    
    # Get all unique staff members from roster (by steam_id)
    staff_data = {}
    for roster in StaffRoster.objects.all():
        if not roster.steam_id:
            continue
            
        if roster.steam_id not in staff_data:
            staff_data[roster.steam_id] = {
                'steam_id': roster.steam_id,
                'name': roster.name,
                'discord_id': roster.discord_id,
                'discord_tag': roster.discord_tag,
                'staff_status': 'active' if roster.is_active else 'inactive',
                'current_role': roster.rank if roster.is_active else '',
                'current_role_priority': roster.rank_priority if roster.is_active else 999,
                'user_id': roster.user_id if roster.user_id else None,
                'last_seen': roster.last_seen,
            }
    
    # Create Staff records
    for steam_id, data in staff_data.items():
        Staff.objects.create(**data)


def reverse_populate(apps, schema_editor):
    """Reverse migration - delete all Staff records."""
    Staff = apps.get_model('staff', 'Staff')
    Staff.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0007_create_staff_model'),
    ]

    operations = [
        migrations.RunPython(populate_staff_from_roster, reverse_populate),
    ]
