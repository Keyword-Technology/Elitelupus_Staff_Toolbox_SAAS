import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.servers.models import ServerPlayer
from apps.staff.models import StaffRoster

print("=== All ServerPlayer records ===")
all_players = ServerPlayer.objects.all()[:10]
for sp in all_players:
    print(f'  {sp.name}, is_staff={sp.is_staff}, staff_rank={sp.staff_rank}')

print("\n=== StaffRoster names (lowercase) ===")
roster = StaffRoster.objects.filter(is_active=True)[:10]
roster_names = [r.name.lower() for r in roster]
print(roster_names)

print("\n=== Checking player name matches ===")
for sp in all_players:
    player_lower = sp.name.lower()
    matched = player_lower in roster_names
    print(f'Player "{sp.name}" -> "{player_lower}" matched: {matched}')
