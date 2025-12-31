"""
Management command to link existing Steam and Discord accounts based on staff roster.
Usage: python manage.py link_accounts
"""
import logging

from apps.staff.models import StaffRoster
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Link existing Steam and Discord accounts based on staff roster data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be linked without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.SUCCESS('Starting account linking process...'))
        
        linked_count = 0
        skipped_count = 0
        
        # Get all active roster entries that have both Steam and Discord IDs
        roster_entries = StaffRoster.objects.filter(
            is_active=True
        ).exclude(steam_id__isnull=True).exclude(steam_id='').exclude(
            discord_id__isnull=True
        ).exclude(discord_id='')
        
        self.stdout.write(f'Found {roster_entries.count()} roster entries with both Steam and Discord IDs')
        
        for roster in roster_entries:
            # Find Steam user
            steam_user = User.objects.filter(steam_id=roster.steam_id).first()
            
            # Find Discord user
            discord_user = User.objects.filter(discord_id=roster.discord_id).first()
            
            # Case 1: Both users exist and are different - merge Discord into Steam account
            if steam_user and discord_user and steam_user.id != discord_user.id:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nFound separate accounts for {roster.name}:'
                    )
                )
                self.stdout.write(f'  Steam account: {steam_user.username} (ID: {steam_user.id})')
                self.stdout.write(f'  Discord account: {discord_user.username} (ID: {discord_user.id})')
                
                if not dry_run:
                    # Link Discord info to Steam account
                    steam_user.discord_id = roster.discord_id
                    steam_user.discord_username = discord_user.discord_username
                    steam_user.discord_discriminator = discord_user.discord_discriminator
                    steam_user.discord_avatar = discord_user.discord_avatar
                    
                    # If Steam account doesn't have display name, use Discord's
                    if not steam_user.display_name and discord_user.display_name:
                        steam_user.display_name = discord_user.display_name
                    
                    steam_user.save()
                    
                    # Deactivate the Discord-only account
                    discord_user.is_active = False
                    discord_user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Linked Discord to Steam account and deactivated Discord-only account'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [DRY RUN] Would link Discord to Steam account'
                        )
                    )
                
                linked_count += 1
            
            # Case 2: Only Steam user exists, no Discord user - add Discord info
            elif steam_user and not discord_user:
                if not steam_user.discord_id:
                    self.stdout.write(
                        f'\nAdding Discord info to {steam_user.username} from roster'
                    )
                    
                    if not dry_run:
                        steam_user.discord_id = roster.discord_id
                        # Don't have username/discriminator from roster, but will be filled on next Discord login
                        steam_user.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Added Discord ID to Steam account'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] Would add Discord ID to Steam account'
                            )
                        )
                    
                    linked_count += 1
                else:
                    skipped_count += 1
            
            # Case 3: Only Discord user exists, no Steam user - add Steam info
            elif discord_user and not steam_user:
                if not discord_user.steam_id:
                    self.stdout.write(
                        f'\nAdding Steam info to {discord_user.username} from roster'
                    )
                    
                    if not dry_run:
                        discord_user.steam_id = roster.steam_id
                        # Steam ID 64 will be filled on next Steam login
                        discord_user.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Added Steam ID to Discord account'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] Would add Steam ID to Discord account'
                            )
                        )
                    
                    linked_count += 1
                else:
                    skipped_count += 1
            
            # Case 4: Account already linked
            elif steam_user and steam_user.discord_id == roster.discord_id:
                skipped_count += 1
            
            # Case 5: Neither user exists yet
            else:
                skipped_count += 1
        
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would have linked {linked_count} accounts'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'COMPLETE: Linked {linked_count} accounts'
                )
            )
        self.stdout.write(f'Skipped: {skipped_count} (already linked or no users yet)')
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nRun without --dry-run to apply these changes'
                )
            )
