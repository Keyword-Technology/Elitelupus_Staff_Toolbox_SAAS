"""
Management command to backfill last_seen timestamps for staff members.
This updates the Staff.last_seen field based on their most recent ServerSession.
"""
from apps.staff.models import ServerSession, Staff
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Backfill last_seen timestamps for staff members based on their server sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no changes will be made\n'))
        
        # Get all staff members
        all_staff = Staff.objects.all()
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write(f'Processing {all_staff.count()} staff members...\n')
        
        for staff in all_staff:
            # Find their most recent session with a leave time
            most_recent_session = ServerSession.objects.filter(
                staff=staff,
                leave_time__isnull=False
            ).order_by('-leave_time').first()
            
            if most_recent_session:
                # Update last_seen if it's None or older than the session leave_time
                if staff.last_seen is None or staff.last_seen < most_recent_session.leave_time:
                    if dry_run:
                        self.stdout.write(
                            f'  Would update {staff.name}: '
                            f'last_seen would be set to {most_recent_session.leave_time}'
                        )
                    else:
                        staff.last_seen = most_recent_session.leave_time
                        staff.save(update_fields=['last_seen'])
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Updated {staff.name}: '
                                f'last_seen set to {most_recent_session.leave_time}'
                            )
                        )
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Would update: {updated_count} staff members'))
            self.stdout.write(f'Would skip: {skipped_count} staff members (no sessions or already up to date)')
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count} staff members'))
            self.stdout.write(f'Skipped: {skipped_count} staff members (no sessions or already up to date)')
        self.stdout.write('=' * 60)
