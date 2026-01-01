# Generated migration for Sit Recording default settings

from django.db import migrations, models


def create_sit_recording_settings(apps, schema_editor):
    """Create default system settings for sit recording feature."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    
    default_settings = [
        {
            'key': 'sit_recording_enabled',
            'value': 'true',
            'setting_type': 'boolean',
            'category': 'sit_recording',
            'description': 'Master toggle to enable/disable the sit recording feature system-wide',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_ocr_enabled',
            'value': 'true',
            'setting_type': 'boolean',
            'category': 'sit_recording',
            'description': 'Enable OCR-based automatic sit detection',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_max_file_size_mb',
            'value': '500',
            'setting_type': 'integer',
            'category': 'sit_recording',
            'description': 'Maximum recording file size in megabytes',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_max_duration_minutes',
            'value': '30',
            'setting_type': 'integer',
            'category': 'sit_recording',
            'description': 'Maximum recording duration in minutes',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_retention_days',
            'value': '30',
            'setting_type': 'integer',
            'category': 'sit_recording',
            'description': 'Number of days to retain sit recordings before automatic deletion',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_allowed_formats',
            'value': '["webm", "mp4"]',
            'setting_type': 'json',
            'category': 'sit_recording',
            'description': 'List of allowed video formats for recordings',
            'is_sensitive': False,
            'is_active': True,
        },
        {
            'key': 'sit_recording_ocr_patterns',
            'value': '{"claim": ["[Elite Reports]", "claimed", "report"], "close": ["[Elite Reports]", "closed", "report"], "rating": ["[Elite Admin Stats]", "credits"]}',
            'setting_type': 'json',
            'category': 'sit_recording',
            'description': 'OCR detection patterns for sit events (JSON object)',
            'is_sensitive': False,
            'is_active': True,
        },
    ]
    
    for setting in default_settings:
        SystemSetting.objects.get_or_create(
            key=setting['key'],
            defaults=setting
        )


def remove_sit_recording_settings(apps, schema_editor):
    """Remove sit recording system settings."""
    SystemSetting = apps.get_model('system_settings', 'SystemSetting')
    SystemSetting.objects.filter(category='sit_recording').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system_settings', '0003_alter_systemsetting_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemsetting',
            name='category',
            field=models.CharField(
                choices=[
                    ('general', 'General'),
                    ('counters', 'Counters & Quotas'),
                    ('api_keys', 'API Keys'),
                    ('database', 'Database'),
                    ('cache', 'Cache'),
                    ('external', 'External Services'),
                    ('game_servers', 'Game Servers'),
                    ('sit_recording', 'Sit Recording'),
                ],
                default='general',
                max_length=50,
            ),
        ),
        migrations.RunPython(create_sit_recording_settings, remove_sit_recording_settings),
    ]
