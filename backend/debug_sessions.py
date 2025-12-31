import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.servers.models import ServerPlayer
from apps.staff.models import ServerSession, StaffRoster

print("=== ServerPlayer Debug ===")
staff_players = ServerPlayer.objects.filter(is_staff=True)
print(f'Staff players found: {staff_players.count()}')
for sp in list(staff_players[:5]):
    print(f'  {sp.name}, is_staff={sp.is_staff}, steam_id={sp.steam_id}')

print("\n=== StaffRoster Debug ===")
roster = StaffRoster.objects.filter(is_active=True)[:5]
for r in roster:
    print(f'  {r.name}, steam_id={r.steam_id}')

print(f"\n=== Total Sessions: {ServerSession.objects.count()} ===")

# Check name matching
print("\n=== Name Matching Test ===")
staff_dict = {entry.name.lower(): entry for entry in StaffRoster.objects.filter(is_active=True)}
for sp in list(staff_players[:5]):
    player_name_lower = sp.name.lower()
    matched = player_name_lower in staff_dict
    print(f'Player "{sp.name}" (lower: "{player_name_lower}") matched: {matched}')
    if matched:
        staff_entry = staff_dict[player_name_lower]
        print(f'  -> Matched to: {staff_entry.name}, steam_id={staff_entry.steam_id}')
