# Migration to refactor StaffRoster to link to Staff

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0001_initial'),  # Need for ServerSession/ServerSessionAggregate
        ('staff', '0008_populate_staff_table'),
    ]

    operations = [
        # Add staff foreign key to StaffRoster (nullable first)
        migrations.AddField(
            model_name='staffroster',
            name='staff',
            field=models.ForeignKey(
                null=True,  # Temporarily nullable
                on_delete=django.db.models.deletion.CASCADE,
                related_name='roster_entries',
                to='staff.staff',
                to_field='steam_id'
            ),
        ),
        # Populate staff foreign key from steam_id
        migrations.RunPython(
            lambda apps, schema_editor: populate_staff_fk(apps, schema_editor),
            reverse_code=migrations.RunPython.noop,
        ),
        # Make staff foreign key non-nullable
        migrations.AlterField(
            model_name='staffroster',
            name='staff',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='roster_entries',
                to='staff.staff',
                to_field='steam_id'
            ),
        ),
        # Remove old fields from StaffRoster
        migrations.RemoveField(
            model_name='staffroster',
            name='name',
        ),
        migrations.RemoveField(
            model_name='staffroster',
            name='steam_id',
        ),
        migrations.RemoveField(
            model_name='staffroster',
            name='discord_id',
        ),
        migrations.RemoveField(
            model_name='staffroster',
            name='discord_tag',
        ),
        migrations.RemoveField(
            model_name='staffroster',
            name='last_seen',
        ),
        migrations.RemoveField(
            model_name='staffroster',
            name='user',
        ),
        # Update ServerSession to reference Staff instead of StaffRoster
        migrations.AlterField(
            model_name='serversession',
            name='staff',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='server_sessions',
                to='staff.staff',
                to_field='steam_id',
                verbose_name='Staff Member'
            ),
        ),
        # Update ServerSessionAggregate to reference Staff
        migrations.AlterField(
            model_name='serversessionaggregate',
            name='staff',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='session_aggregates',
                to='staff.staff',
                to_field='steam_id',
                verbose_name='Staff Member'
            ),
        ),
        # Update StaffHistoryEvent to reference Staff
        migrations.AlterField(
            model_name='staffhistoryevent',
            name='staff',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='history_events',
                to='staff.staff',
                to_field='steam_id',
                verbose_name='Staff Member'
            ),
        ),
        # Update StaffRoster meta
        migrations.AlterModelOptions(
            name='staffroster',
            options={
                'ordering': ['rank_priority', 'staff__name'],
                'verbose_name': 'Roster Entry',
                'verbose_name_plural': 'Staff Roster'
            },
        ),
        migrations.AlterUniqueTogether(
            name='staffroster',
            unique_together={('staff', 'is_active')},
        ),
    ]


def populate_staff_fk(apps, schema_editor):
    """Link StaffRoster entries to Staff via steam_id."""
    StaffRoster = apps.get_model('staff', 'StaffRoster')
    Staff = apps.get_model('staff', 'Staff')
    
    for roster in StaffRoster.objects.filter(staff__isnull=True):
        if roster.steam_id:
            staff = Staff.objects.filter(steam_id=roster.steam_id).first()
            if staff:
                roster.staff = staff
                roster.save()
