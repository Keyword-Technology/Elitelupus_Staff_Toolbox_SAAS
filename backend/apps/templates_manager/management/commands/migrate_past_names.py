"""
Migrate existing search history to past_names field
"""
from apps.templates_manager.models import (SteamProfileHistory,
                                           SteamProfileSearch)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Migrate search history persona names to past_names field'

    def handle(self, *args, **options):
        profiles = SteamProfileSearch.objects.all()
        count = 0
        
        for profile in profiles:
            # Get all unique names from history
            history = SteamProfileHistory.objects.filter(
                search=profile
            ).order_by('searched_at')
            
            # Initialize past_names if needed
            if not isinstance(profile.past_names, list):
                profile.past_names = []
            
            # Get existing names in past_names
            existing_names = {entry['name'] for entry in profile.past_names if isinstance(entry, dict)}
            
            # Add names from history
            for h in history:
                if h.persona_name and h.persona_name.strip() and h.persona_name not in existing_names:
                    profile.past_names.append({
                        'name': h.persona_name,
                        'first_seen': h.searched_at.isoformat(),
                        'last_seen': h.searched_at.isoformat()
                    })
                    existing_names.add(h.persona_name)
            
            # Add current name if not in past_names
            if profile.persona_name and profile.persona_name not in existing_names:
                profile.past_names.append({
                    'name': profile.persona_name,
                    'first_seen': profile.first_searched_at.isoformat() if profile.first_searched_at else profile.last_searched_at.isoformat(),
                    'last_seen': profile.last_searched_at.isoformat()
                })
            
            if profile.past_names:
                profile.save()
                count += 1
                self.stdout.write(f'Updated {profile.steam_id_64}: {len(profile.past_names)} past names')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated {count} profiles'))
