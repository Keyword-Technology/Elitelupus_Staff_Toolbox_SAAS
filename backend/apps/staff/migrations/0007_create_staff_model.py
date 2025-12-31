# Generated migration to create Staff model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('staff', '0006_staffhistoryevent'),
    ]

    operations = [
        # Step 1: Create the Staff model
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('steam_id', models.CharField(max_length=50, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('discord_id', models.CharField(blank=True, max_length=50, null=True)),
                ('discord_tag', models.CharField(blank=True, max_length=100, null=True)),
                ('staff_status', models.CharField(
                    choices=[('active', 'Active Staff'), ('inactive', 'Inactive/Removed'), ('loa', 'Leave of Absence')],
                    default='active',
                    max_length=20
                )),
                ('current_role', models.CharField(blank=True, max_length=50)),
                ('current_role_priority', models.IntegerField(default=999)),
                ('first_joined', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(blank=True, null=True)),
                ('staff_since', models.DateTimeField(blank=True, null=True)),
                ('staff_left_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='staff_profile',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Staff Member',
                'verbose_name_plural': 'Staff Members',
                'ordering': ['current_role_priority', 'name'],
            },
        ),
    ]
