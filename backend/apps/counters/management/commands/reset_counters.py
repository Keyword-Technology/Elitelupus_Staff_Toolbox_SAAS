from apps.counters.models import Counter, CounterHistory, CounterSnapshot
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Reset all counters to 0'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the reset operation',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will reset all counters to 0 and clear counter history.\n'
                    'Run with --confirm flag to proceed.'
                )
            )
            return

        try:
            # Reset all counter counts to 0
            Counter.objects.all().update(count=0)
            counter_count = Counter.objects.count()
            
            # Clear counter history
            history_count = CounterHistory.objects.count()
            CounterHistory.objects.all().delete()
            
            # Clear counter snapshots
            snapshot_count = CounterSnapshot.objects.count()
            CounterSnapshot.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Reset complete:\n'
                    f'  - {counter_count} counters set to 0\n'
                    f'  - {history_count} history entries deleted\n'
                    f'  - {snapshot_count} snapshots deleted'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
