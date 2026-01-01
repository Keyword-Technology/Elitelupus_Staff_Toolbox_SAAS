# Generated migration for Sit Recording System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reporter_name', models.CharField(blank=True, max_length=100)),
                ('reported_player', models.CharField(blank=True, max_length=100)),
                ('report_type', models.CharField(blank=True, choices=[('rdm', 'RDM'), ('nlr', 'NLR'), ('rda', 'RDA'), ('failrp', 'FailRP'), ('propblock', 'Prop Block/Abuse'), ('harassment', 'Harassment'), ('other', 'Other')], max_length=50)),
                ('report_reason', models.TextField(blank=True)),
                ('started_at', models.DateTimeField()),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('outcome', models.CharField(blank=True, choices=[('no_action', 'No Action Taken'), ('false_report', 'False Report'), ('verbal_warning', 'Verbal Warning'), ('formal_warning', 'Formal Warning'), ('kick', 'Kick'), ('ban', 'Ban'), ('escalated', 'Escalated to Higher Staff'), ('other', 'Other')], max_length=50)),
                ('outcome_notes', models.TextField(blank=True)),
                ('ban_duration', models.CharField(blank=True, max_length=50)),
                ('player_rating', models.IntegerField(blank=True, null=True)),
                ('player_rating_credits', models.IntegerField(blank=True, null=True)),
                ('detection_method', models.CharField(choices=[('manual', 'Manual (Button Click)'), ('ocr_chat', 'OCR - Chat Detection'), ('ocr_popup', 'OCR - Popup Detection')], default='manual', max_length=20)),
                ('has_recording', models.BooleanField(default=False)),
                ('recording_file', models.FileField(blank=True, null=True, upload_to='sit_recordings/%Y/%m/%d/')),
                ('recording_size_bytes', models.BigIntegerField(blank=True, null=True)),
                ('recording_duration_seconds', models.IntegerField(blank=True, null=True)),
                ('recording_thumbnail', models.ImageField(blank=True, null=True, upload_to='sit_thumbnails/%Y/%m/%d/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('counter_history', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sit_record', to='counters.counterhistory')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sit',
                'verbose_name_plural': 'Sits',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSitPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recording_enabled', models.BooleanField(default=True, help_text='Enable screen recording during sits')),
                ('ocr_enabled', models.BooleanField(default=True, help_text='Enable OCR auto-detection of sit events')),
                ('auto_start_recording', models.BooleanField(default=True, help_text='Automatically start recording when sit is detected')),
                ('auto_stop_recording', models.BooleanField(default=True, help_text='Automatically stop recording when sit is closed')),
                ('ocr_scan_interval_ms', models.IntegerField(default=1500, help_text='Milliseconds between OCR scans')),
                ('ocr_popup_region_enabled', models.BooleanField(default=True, help_text='Scan report popup area for detection')),
                ('ocr_chat_region_enabled', models.BooleanField(default=True, help_text='Scan chat area for detection')),
                ('video_quality', models.CharField(choices=[('low', 'Low (1 Mbps)'), ('medium', 'Medium (2.5 Mbps)'), ('high', 'High (5 Mbps)')], default='medium', max_length=20)),
                ('max_recording_minutes', models.IntegerField(default=30, help_text='Maximum recording duration in minutes')),
                ('show_recording_preview', models.BooleanField(default=True, help_text='Show small preview of recording in UI')),
                ('confirm_before_start', models.BooleanField(default=False, help_text='Show confirmation popup before auto-starting recording')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sit_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Sit Preferences',
                'verbose_name_plural': 'User Sit Preferences',
            },
        ),
        migrations.CreateModel(
            name='SitRecordingChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_number', models.IntegerField()),
                ('chunk_file', models.FileField(upload_to='sit_recording_chunks/')),
                ('size_bytes', models.IntegerField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('sit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recording_chunks', to='counters.sit')),
            ],
            options={
                'ordering': ['chunk_number'],
                'unique_together': {('sit', 'chunk_number')},
            },
        ),
        migrations.CreateModel(
            name='SitNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_type', models.CharField(choices=[('general', 'General Note'), ('steam_id', 'Steam ID'), ('evidence', 'Evidence'), ('action', 'Action Taken')], default='general', max_length=20)),
                ('content', models.TextField()),
                ('steam_id', models.CharField(blank=True, max_length=50)),
                ('steam_profile_url', models.URLField(blank=True)),
                ('steam_persona_name', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='counters.sit')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
