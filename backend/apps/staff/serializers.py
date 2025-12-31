from django.conf import settings
from rest_framework import serializers

from .models import StaffRoster, StaffSyncLog


class StaffRosterSerializer(serializers.ModelSerializer):
    """Serializer for staff roster entries."""
    
    # Map backend field names to frontend expectations
    role = serializers.CharField(source='rank', read_only=True)
    role_color = serializers.ReadOnlyField(source='rank_color')
    role_priority = serializers.IntegerField(source='rank_priority', read_only=True)
    username = serializers.CharField(source='name', read_only=True)
    display_name = serializers.CharField(source='name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    user_avatar = serializers.URLField(source='user.avatar_url', read_only=True, allow_null=True)
    
    # Online status fields
    is_online = serializers.SerializerMethodField()
    server_name = serializers.SerializerMethodField()
    server_id = serializers.SerializerMethodField()
    
    # Discord status fields (optional - requires bot)
    discord_status_display = serializers.CharField(source='discord_status', read_only=True)
    
    # In-app activity (fallback when Discord bot not configured)
    last_seen_display = serializers.SerializerMethodField()
    is_active_display = serializers.SerializerMethodField()
    
    # LOA fields (set to default values for now since not in model)
    is_on_loa = serializers.SerializerMethodField()
    loa_end_date = serializers.SerializerMethodField()
    joined_date = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'username', 'display_name', 'role', 'role_color', 'role_priority',
            'last_seen', 'is_active_in_app', 'last_seen_display', 'is_active_display',
            'is_active', 'is_on_loa', 'loa_end_date',
            'user_id', 'user_avatar', 'last_synced',
            'joined_date', 'last_activity',
            'is_online', 'server_name', 'server_id'
        ]
        read_only_fields = ['last_synced', 'discord_status_updated', 'last_seen', 'is_active_in_app
            'joined_date', 'last_activity',
            'is_online', 'server_name', 'server_id'
        ]
        read_only_fields = ['last_synced', 'discord_status_updated']
    
    def get_is_online(self, obj):
        """Check if staff member is currently online on any server."""
        from apps.servers.models import ServerPlayer
        return ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).exists()
    
    def get_server_name(self, obj):
        """Get the server name where staff member is online."""
        from apps.servers.models import ServerPlayer
        player = ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).first()
        return player.server.name if player else None
    
    def get_server_id(self, obj):
        """Get the server ID where staff member is online."""
        from apps.servers.models import ServerPlayer
        player = ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).first()
        return player.server.id if player else None
    
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
        ""Use last_seen if available, otherwise fall back to last_synced
        if obj.last_seen:
            return obj.last_seen.isoformat()
        return obj.last_synced.isoformat() if obj.last_synced else None
    
    def get_last_seen_display(self, obj):
        """Get human-readable last seen time."""
        if not obj.last_seen:
            return None
        
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.last_seen
        
        if diff < timedelta(minutes=5):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = diff.days
            return f"{days}d ago"
    
    def get_is_active_display(self, obj):
        """Check if user is currently active (seen in last 5 minutes)."""
        if not obj.last_seen:
            return False
        
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        return (now - obj.last_seen) < timedelta(minutes=5)
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
