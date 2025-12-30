from rest_framework import serializers
from django.conf import settings
from .models import StaffRoster, StaffSyncLog


class StaffRosterSerializer(serializers.ModelSerializer):
    """Serializer for staff roster entries."""
    
    rank_color = serializers.ReadOnlyField()
    rank_priority = serializers.ReadOnlyField()
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    user_avatar = serializers.URLField(source='user.avatar_url', read_only=True, allow_null=True)
    
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'rank', 'timezone', 'active_time', 'name',
            'steam_id', 'discord_id', 'discord_tag',
            'rank_color', 'rank_priority', 'is_active',
            'user_id', 'user_avatar', 'last_synced'
        ]
        read_only_fields = ['last_synced']


class StaffSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for sync log entries."""
    
    class Meta:
        model = StaffSyncLog
        fields = '__all__'


class StaffDistributionSerializer(serializers.Serializer):
    """Serializer for staff distribution data."""
    
    server_1 = serializers.ListField(child=StaffRosterSerializer())
    server_2 = serializers.ListField(child=StaffRosterSerializer())
    offline = serializers.ListField(child=StaffRosterSerializer())


class RolePrioritySerializer(serializers.Serializer):
    """Serializer for role priorities."""
    
    role = serializers.CharField()
    priority = serializers.IntegerField()
    color = serializers.CharField()
