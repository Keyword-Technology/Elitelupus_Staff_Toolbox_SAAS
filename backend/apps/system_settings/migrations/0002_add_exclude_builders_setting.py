# Generated migration to add exclude_builders system setting

from django.db import migrations


def add_exclude_builders_setting(apps, schema_editor):
    """Add the exclude_builders system setting."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    
    # Only create if doesn't exist
    if not SystemSetting.objects.filter(key='exclude_builders').exists():
        SystemSetting.objects.create(
            key='exclude_builders',
            value='true',
            setting_type='boolean',
            category='general',
            description='Exclude builders from staff lists, leaderboards, and online indicators. When enabled, any staff member with "Builder" in their role name will be hidden from all staff-related displays.',
            is_sensitive=False,
            is_active=True
        )


def reverse_exclude_builders_setting(apps, schema_editor):
    """Remove the exclude_builders system setting."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    SystemSetting.objects.filter(key='exclude_builders').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system_settings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_exclude_builders_setting, reverse_exclude_builders_setting),
    ]
