from rest_framework import serializers
from django.conf import settings
from .models import StaffRoster, StaffSyncLog


class StaffRosterSerializer(serializers.ModelSerializer):
    """Serializer for staff roster entries."""
    
    # Map backend field names to frontend expectations
    role = serializers.CharField(source='rank', read_only=True)
    role_color = serializers.ReadOnlyField(source='rank_color')
    role_priority = serializers.ReadOnlyField(source='rank_priority')
    username = serializers.CharField(source='name', read_only=True)
    display_name = serializers.CharField(source='name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    user_avatar = serializers.URLField(source='user.avatar_url', read_only=True, allow_null=True)
    
    # LOA fields (set to default values for now since not in model)
    is_on_loa = serializers.SerializerMethodField()
    loa_end_date = serializers.SerializerMethodField()
    joined_date = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'username', 'display_name', 'role', 'role_color', 'role_priority',
            'rank', 'timezone', 'active_time', 'name',
            'steam_id', 'discord_id', 'discord_tag',
            'is_active', 'is_on_loa', 'loa_end_date',
            'user_id', 'user_avatar', 'last_synced',
            'joined_date', 'last_activity'
        ]
        read_only_fields = ['last_synced']
    
    def get_is_on_loa(self, obj):
        """Check if staff member is on LOA (Leave of Absence)."""
        # TODO: Implement LOA tracking in model
        return False
    
    def get_loa_end_date(self, obj):
        """Get LOA end date."""
        # TODO: Implement LOA tracking in model
        return None
    
    def get_joined_date(self, obj):
        """Get joined date - use last_synced as fallback."""
        # TODO: Add proper joined_date field to model
        return obj.last_synced.isoformat() if obj.last_synced else None
    
    def get_last_activity(self, obj):
        """Get last activity date."""
        # TODO: Implement activity tracking
        return obj.last_synced.isoformat() if obj.last_synced else None


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
