from django.contrib import admin
from .models import GameServer, ServerPlayer, ServerStatusLog


@admin.register(GameServer)
class GameServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'port', 'current_players', 'max_players', 
                   'is_online', 'is_active', 'last_query']
    list_filter = ['is_active', 'is_online']
    ordering = ['display_order', 'name']


@admin.register(ServerPlayer)
class ServerPlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'server', 'score', 'duration', 'is_staff', 'staff_rank']
    list_filter = ['server', 'is_staff']
    search_fields = ['name']


@admin.register(ServerStatusLog)
class ServerStatusLogAdmin(admin.ModelAdmin):
    list_display = ['server', 'timestamp', 'player_count', 'staff_count', 'is_online']
    list_filter = ['server', 'is_online']
    ordering = ['-timestamp']
