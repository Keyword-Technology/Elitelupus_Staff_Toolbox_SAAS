# Migration to refactor StaffRoster to link to Staff

import django.db.models.deletion
from django.db import migrations, models


def populate_staff_fk_roster(apps, schema_editor):
    """Link StaffRoster entries to Staff via steam_id."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Update StaffRoster.staff_id from steam_id
        cursor.execute("""
            UPDATE staff_staffroster
            SET staff_id = staff_staffroster.steam_id
            WHERE staff_id IS NULL;
        """)


def convert_serversession_staff_ids(apps, schema_editor):
    """Convert ServerSession.staff_id from integer (StaffRoster.id) to steam_id (Staff.steam_id)."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Update ServerSession.staff_id by looking up steam_id from StaffRoster
        cursor.execute("""
            UPDATE staff_serversession
            SET staff_id_temp = sr.steam_id
            FROM staff_staffroster sr
            WHERE staff_serversession.staff_id = sr.id;
        """)


def convert_sessionaggregate_staff_ids(apps, schema_editor):
    """Convert ServerSessionAggregate.staff_id from integer to steam_id."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Update ServerSessionAggregate.staff_id
        cursor.execute("""
            UPDATE staff_serversessionaggregate
            SET staff_id_temp = sr.steam_id
            FROM staff_staffroster sr
            WHERE staff_serversessionaggregate.staff_id = sr.id;
        """)


def convert_historyevent_staff_ids(apps, schema_editor):
    """Convert StaffHistoryEvent.staff_id from integer to steam_id."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Update StaffHistoryEvent.staff_id
        cursor.execute("""
            UPDATE staff_staffhistoryevent
            SET staff_id_temp = sr.steam_id
            FROM staff_staffroster sr
            WHERE staff_staffhistoryevent.staff_id = sr.id;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0001_initial'),
        ('staff', '0008_populate_staff_table'),
    ]

    operations = [
        # ======================================================================
        # STEP 1: Add temporary foreign keys (nullable) and temp columns
        # ======================================================================
        
        # Add staff foreign key to StaffRoster (nullable first)
        migrations.AddField(
            model_name='staffroster',
            name='staff',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='roster_entries',
                to='staff.staff',
                to_field='steam_id',
                db_column='staff_id'  # Use staff_id as column name
            ),
        ),
        
        # Add temporary staff_id_temp columns for data conversion
        migrations.RunSQL(
            sql=[
                'ALTER TABLE staff_serversession ADD COLUMN staff_id_temp VARCHAR(50);',
                'ALTER TABLE staff_serversessionaggregate ADD COLUMN staff_id_temp VARCHAR(50);',
                'ALTER TABLE staff_staffhistoryevent ADD COLUMN staff_id_temp VARCHAR(50);',
            ],
            reverse_sql=[
                'ALTER TABLE staff_serversession DROP COLUMN staff_id_temp;',
                'ALTER TABLE staff_serversessionaggregate DROP COLUMN staff_id_temp;',
                'ALTER TABLE staff_staffhistoryevent DROP COLUMN staff_id_temp;',
            ]
        ),
        
        # ======================================================================
        # STEP 2: Populate the new foreign keys
        # ======================================================================
        
        # Populate StaffRoster.staff from steam_id
        migrations.RunPython(
            populate_staff_fk_roster,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Convert ServerSession staff_id integers to steam_ids
        migrations.RunPython(
            convert_serversession_staff_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Convert ServerSessionAggregate staff_id integers to steam_ids
        migrations.RunPython(
            convert_sessionaggregate_staff_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Convert StaffHistoryEvent staff_id integers to steam_ids
        migrations.RunPython(
            convert_historyevent_staff_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # ======================================================================
        # STEP 3: Drop old staff_id columns and rename temp columns
        # ======================================================================
        
        migrations.RunSQL(
            sql=[
                # ServerSession
                'ALTER TABLE staff_serversession DROP CONSTRAINT IF EXISTS staff_serversession_staff_id_d40b042d_fk_staff_staff_steam_id CASCADE;',
                'ALTER TABLE staff_serversession DROP COLUMN staff_id;',
                'ALTER TABLE staff_serversession RENAME COLUMN staff_id_temp TO staff_id;',
                
                # ServerSessionAggregate
                'ALTER TABLE staff_serversessionaggregate DROP CONSTRAINT IF EXISTS staff_serversessionaggregate_staff_id_8a0b042d_fk_staff_staff_steam_id CASCADE;',
                'ALTER TABLE staff_serversessionaggregate DROP COLUMN staff_id;',
                'ALTER TABLE staff_serversessionaggregate RENAME COLUMN staff_id_temp TO staff_id;',
                
                # StaffHistoryEvent
                'ALTER TABLE staff_staffhistoryevent DROP CONSTRAINT IF EXISTS staff_staffhistoryevent_staff_id_7b1c042d_fk_staff_staff_steam_id CASCADE;',
                'ALTER TABLE staff_staffhistoryevent DROP COLUMN staff_id;',
                'ALTER TABLE staff_staffhistoryevent RENAME COLUMN staff_id_temp TO staff_id;',
            ],
            reverse_sql=migrations.RunSQL.noop
        ),
        
        # ======================================================================
        # STEP 4: Add foreign key constraints back
        # ======================================================================
        
        migrations.RunSQL(
            sql=[
                'ALTER TABLE staff_serversession ADD CONSTRAINT staff_serversession_staff_id_fk FOREIGN KEY (staff_id) REFERENCES staff_staff(steam_id) DEFERRABLE INITIALLY DEFERRED;',
                'ALTER TABLE staff_serversessionaggregate ADD CONSTRAINT staff_serversessionaggregate_staff_id_fk FOREIGN KEY (staff_id) REFERENCES staff_staff(steam_id) DEFERRABLE INITIALLY DEFERRED;',
                'ALTER TABLE staff_staffhistoryevent ADD CONSTRAINT staff_staffhistoryevent_staff_id_fk FOREIGN KEY (staff_id) REFERENCES staff_staff(steam_id) DEFERRABLE INITIALLY DEFERRED;',
            ],
            reverse_sql=migrations.RunSQL.noop
        ),
        
        # ======================================================================
        # STEP 5: Make StaffRoster.staff non-nullable and clean up old fields
        # ======================================================================
        
        migrations.AlterField(
            model_name='staffroster',
            name='staff',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='roster_entries',
                to='staff.staff',
                to_field='steam_id',
                db_column='staff_id'
            ),
        ),
        
        # Remove old fields from StaffRoster
        migrations.RemoveField(model_name='staffroster', name='name'),
        migrations.RemoveField(model_name='staffroster', name='steam_id'),
        migrations.RemoveField(model_name='staffroster', name='discord_id'),
        migrations.RemoveField(model_name='staffroster', name='discord_tag'),
        migrations.RemoveField(model_name='staffroster', name='last_seen'),
        migrations.RemoveField(model_name='staffroster', name='user'),
        
        # ======================================================================
        # STEP 6: Update meta options
        # ======================================================================
        
        migrations.AlterModelOptions(
            name='staffroster',
            options={
                'ordering': ['rank_priority'],
                'verbose_name': 'Roster Entry',
                'verbose_name_plural': 'Staff Roster'
            },
        ),
    ]
