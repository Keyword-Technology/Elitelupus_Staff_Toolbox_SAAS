"""
Management command to test server status query with staff matching.
This will query the servers and show which staff members are detected as online.
"""
from django.core.management.base import BaseCommand
from apps.servers.services import ServerQueryService
from apps.servers.models import GameServer, ServerPlayer
from apps.staff.models import StaffRoster


class Command(BaseCommand):
    help = 'Query servers and display staff detection results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server-id',
            type=int,
            help='Query specific server by ID',
        )

    def handle(self, *args, **options):
        service = ServerQueryService()
        
        # Get servers to query
        if options['server_id']:
            servers = GameServer.objects.filter(id=options['server_id'], is_active=True)
        else:
            servers = GameServer.objects.filter(is_active=True)
        
        if not servers.exists():
            self.stdout.write(self.style.ERROR('No active servers found'))
            return
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Server Status Query with Staff Detection'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        for server in servers:
            self.stdout.write(f'\n{self.style.WARNING(f"Querying: {server.name}")}')
            self.stdout.write(f'Address: {server.ip_address}:{server.port}')
            
            # Query the server
            status = service.query_server(server)
            
            if not status.get('online'):
                self.stdout.write(self.style.ERROR(f'  ✗ Server is offline'))
                self.stdout.write(self.style.ERROR(f'  Error: {status.get("error")}'))
                continue
            
            # Display server info
            self.stdout.write(self.style.SUCCESS(f'  ✓ Server is online'))
            self.stdout.write(f'  Server Name: {status.get("server_name")}')
            self.stdout.write(f'  Map: {status.get("map")}')
            self.stdout.write(f'  Players: {status.get("players")} / {status.get("max_players")}')
            
            # Get players on this server
            players = ServerPlayer.objects.filter(server=server).order_by('-is_staff', 'name')
            
            if not players.exists():
                self.stdout.write('  No players currently online')
                continue
            
            # Display staff members
            staff_players = players.filter(is_staff=True)
            if staff_players.exists():
                self.stdout.write(f'\n  {self.style.SUCCESS(f"Staff Online ({staff_players.count()}):")}')
                for player in staff_players:
                    duration = player.duration_formatted
                    self.stdout.write(
                        f'    ✓ {player.name} ({player.staff_rank}) - {duration}'
                    )
            else:
                self.stdout.write('  No staff members online')
            
            # Display regular players
            regular_players = players.filter(is_staff=False)
            if regular_players.exists():
                self.stdout.write(f'\n  {self.style.WARNING(f"Regular Players ({regular_players.count()}):")}')
                for player in regular_players[:10]:  # Show first 10
                    duration = player.duration_formatted
                    self.stdout.write(f'    - {player.name} - {duration}')
                
                if regular_players.count() > 10:
                    self.stdout.write(f'    ... and {regular_players.count() - 10} more')
        
        # Show staff roster summary
        self.stdout.write(f'\n{self.style.SUCCESS("=" * 70)}')
        self.stdout.write(self.style.SUCCESS('Staff Roster Summary'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        all_staff = StaffRoster.objects.filter(is_active=True).order_by('rank_priority')
        online_staff_ids = set(
            ServerPlayer.objects.filter(is_staff=True)
            .values_list('steam_id', flat=True)
        )
        
        online_count = 0
        offline_count = 0
        
        self.stdout.write(f'\n{self.style.SUCCESS("Online Staff:")}')
        for staff in all_staff:
            if staff.steam_id and staff.steam_id in online_staff_ids:
                online_count += 1
                # Find which server they're on
                player = ServerPlayer.objects.filter(steam_id=staff.steam_id).first()
                server_name = player.server.name if player else 'Unknown'
                self.stdout.write(f'  ✓ {staff.name} ({staff.rank}) - {server_name}')
        
        if online_count == 0:
            self.stdout.write('  No staff members online')
        
        self.stdout.write(f'\n{self.style.WARNING("Offline Staff:")}')
        for staff in all_staff:
            if not staff.steam_id or staff.steam_id not in online_staff_ids:
                offline_count += 1
                if offline_count <= 5:  # Show first 5
                    self.stdout.write(f'  - {staff.name} ({staff.rank})')
        
        if offline_count > 5:
            self.stdout.write(f'  ... and {offline_count - 5} more')
        
        self.stdout.write(f'\n{self.style.SUCCESS("=" * 70)}')
        self.stdout.write(f'Total Staff: {all_staff.count()} | Online: {online_count} | Offline: {offline_count}')
        self.stdout.write(self.style.SUCCESS('=' * 70))
