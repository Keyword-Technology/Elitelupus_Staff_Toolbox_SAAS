from rest_framework import serializers
from .models import GameServer, ServerPlayer, ServerStatusLog


class ServerPlayerSerializer(serializers.ModelSerializer):
    """Serializer for server players."""
    
    duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = ServerPlayer
        fields = [
            'id', 'name', 'score', 'duration', 'duration_formatted',
            'is_staff', 'staff_rank', 'steam_id'
        ]


class GameServerSerializer(serializers.ModelSerializer):
    """Serializer for game servers."""
    
    players = ServerPlayerSerializer(many=True, read_only=True)
    
    class Meta:
        model = GameServer
        fields = [
            'id', 'name', 'ip_address', 'port', 'is_active',
            'server_name', 'map_name', 'max_players', 'current_players',
            'is_online', 'last_query', 'last_successful_query',
            'players'
        ]


class ServerStatusSerializer(serializers.Serializer):
    """Serializer for server status response."""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    server_name = serializers.CharField()
    map_name = serializers.CharField()
    current_players = serializers.IntegerField()
    max_players = serializers.IntegerField()
    is_online = serializers.BooleanField()
    staff_online = serializers.IntegerField()
    players = ServerPlayerSerializer(many=True)


class StaffDistributionSerializer(serializers.Serializer):
    """Serializer for staff distribution data."""
    
    server_1 = serializers.ListField()
    server_2 = serializers.ListField()
    offline = serializers.ListField()


class ServerStatusLogSerializer(serializers.ModelSerializer):
    """Serializer for status logs."""
    
    class Meta:
        model = ServerStatusLog
        fields = '__all__'
