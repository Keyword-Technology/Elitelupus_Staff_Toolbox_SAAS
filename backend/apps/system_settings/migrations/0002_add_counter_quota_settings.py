# Generated migration to add counter quota settings

from django.db import migrations


def create_quota_settings(apps, schema_editor):
    """Create default quota settings for sits and tickets."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    
    # Create sit quota setting
    SystemSetting.objects.get_or_create(
        key='counter_sit_quota',
        defaults={
            'value': '25',
            'setting_type': 'integer',
            'category': 'counters',
            'description': 'Daily sit quota target for staff members. Staff are expected to complete this many sits per day.',
            'is_sensitive': False,
            'is_active': True,
        }
    )
    
    # Create ticket quota setting
    SystemSetting.objects.get_or_create(
        key='counter_ticket_quota',
        defaults={
            'value': '3',
            'setting_type': 'integer',
            'category': 'counters',
            'description': 'Daily ticket quota target for staff members. Staff are expected to complete this many tickets per day.',
            'is_sensitive': False,
            'is_active': True,
        }
    )


def remove_quota_settings(apps, schema_editor):
    """Remove quota settings if migration is reversed."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    SystemSetting.objects.filter(key__in=['counter_sit_quota', 'counter_ticket_quota']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system_settings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_quota_settings, remove_quota_settings),
    ]
