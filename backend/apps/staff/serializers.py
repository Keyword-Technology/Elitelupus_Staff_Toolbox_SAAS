from django.conf import settings
from rest_framework import serializers

from .models import (ServerSession, ServerSessionAggregate, Staff,
                     StaffHistoryEvent, StaffRoster, StaffSyncLog)


class LegacyStaffSerializer(serializers.ModelSerializer):
    """Serializer for legacy/inactive staff members."""
    
    # Map backend field names to frontend expectations
    role = serializers.CharField(source='current_role', read_only=True)
    role_color = serializers.SerializerMethodField()
    role_priority = serializers.IntegerField(source='current_role_priority', read_only=True)
    username = serializers.CharField(source='name', read_only=True)
    display_name = serializers.CharField(source='name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    user_avatar = serializers.URLField(source='user.avatar_url', read_only=True, allow_null=True)
    
    # Status fields
    status_display = serializers.CharField(source='get_staff_status_display', read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'steam_id', 'username', 'display_name', 'role', 'role_color', 'role_priority',
            'discord_id', 'discord_tag', 'staff_status', 'status_display',
            'user_id', 'user_avatar', 'first_joined', 'last_seen',
            'staff_since', 'staff_left_at'
        ]
        read_only_fields = fields
    
    def get_role_color(self, obj):
        """Get color for current role."""
        if obj.current_role:
            return settings.STAFF_ROLE_COLORS.get(obj.current_role, '#808080')
        return '#808080'


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
    last_seen_ago = serializers.SerializerMethodField()
    
    # LOA fields (set to default values for now since not in model)
    is_on_loa = serializers.SerializerMethodField()
    loa_end_date = serializers.SerializerMethodField()
    joined_date = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'username', 'display_name', 'role', 'role_color', 'role_priority',
            'steam_id', 'discord_id', 'discord_tag', 'timezone', 'active_time',
            'last_seen', 'is_active_in_app', 'last_seen_display', 'is_active_display', 'last_seen_ago',
            'is_active', 'is_on_loa', 'loa_end_date',
            'user_id', 'user_avatar', 'last_synced',
            'joined_date', 'last_activity',
            'is_online', 'server_name', 'server_id', 
            'discord_status', 'discord_status_display', 'discord_custom_status', 
            'discord_activity', 'discord_status_updated'
        ]
        read_only_fields = [
            'last_synced', 'discord_status_updated', 'last_seen', 'is_active_in_app',
            'joined_date', 'last_activity',
            'is_online', 'server_name', 'server_id', 'discord_status_display'
        ]
    
    def get_is_online(self, obj):
        """Check if staff member is currently online on any server."""
        from apps.servers.models import ServerPlayer

        # Use steam_id for more reliable matching if available
        if obj.steam_id:
            return ServerPlayer.objects.filter(steam_id=obj.steam_id, is_staff=True).exists()
        
        # Fallback to name matching (exact match only as fallback)
        return ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).exists()
    
    def get_server_name(self, obj):
        """Get the server name where staff member is online."""
        from apps.servers.models import ServerPlayer

        # Use steam_id for more reliable matching if available
        if obj.steam_id:
            player = ServerPlayer.objects.filter(steam_id=obj.steam_id, is_staff=True).first()
        else:
            # Fallback to name matching (exact match only as fallback)
            player = ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).first()
        
        return player.server.name if player else None
    
    def get_server_id(self, obj):
        """Get the server ID where staff member is online."""
        from apps.servers.models import ServerPlayer

        # Use steam_id for more reliable matching if available
        if obj.steam_id:
            player = ServerPlayer.objects.filter(steam_id=obj.steam_id, is_staff=True).first()
        else:
            # Fallback to name matching (exact match only as fallback)
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
        """Use last_seen if available, otherwise fall back to last_synced."""
        if obj.last_seen:
            return obj.last_seen.isoformat()
        return obj.last_synced.isoformat() if obj.last_synced else None
    
    def get_last_seen_ago(self, obj):
        """Get human-readable time since last seen."""
        from datetime import timedelta

        from apps.servers.models import ServerPlayer
        from django.utils import timezone

        # Check if currently online (same logic as get_is_online)
        if obj.steam_id:
            is_online = ServerPlayer.objects.filter(steam_id=obj.steam_id, is_staff=True).exists()
        else:
            is_online = ServerPlayer.objects.filter(name__iexact=obj.name, is_staff=True).exists()
        
        # If currently online, return None (will show "Online" in UI)
        if is_online:
            return None
            
        # Check if staff has a last_seen timestamp
        last_seen = obj.staff.last_seen if hasattr(obj, 'staff') else obj.last_seen
        
        # If no last_seen, check if there are any completed sessions and use the most recent leave_time
        if not last_seen:
            most_recent_session = ServerSession.objects.filter(
                staff=obj.staff if hasattr(obj, 'staff') else obj,
                leave_time__isnull=False
            ).order_by('-leave_time').first()
            
            if most_recent_session:
                last_seen = most_recent_session.leave_time
            else:
                return 'Never'
        
        now = timezone.now()
        diff = now - last_seen
        
        # Calculate time ago in human-readable format
        if diff < timedelta(minutes=1):
            return 'Just now'
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif diff < timedelta(days=7):
            days = int(diff.days)
            return f'{days} day{"s" if days != 1 else ""} ago'
        elif diff < timedelta(days=30):
            weeks = int(diff.days / 7)
            return f'{weeks} week{"s" if weeks != 1 else ""} ago'
        elif diff < timedelta(days=365):
            months = int(diff.days / 30)
            return f'{months} month{"s" if months != 1 else ""} ago'
        else:
            years = int(diff.days / 365)
            return f'{years} year{"s" if years != 1 else ""} ago'
    
    def get_last_seen_display(self, obj):
        """Get human-readable last seen time. Only for staff with linked accounts."""
        # Only show activity for staff with linked user accounts
        if not obj.user or not obj.last_seen:
            return None
        
        from datetime import timedelta

        from django.utils import timezone
        
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
        """Check if user is currently active (seen in last 5 minutes). Only for linked accounts."""
        # Only show activity for staff with linked user accounts
        if not obj.user or not obj.last_seen:
            return False
        
        from datetime import timedelta

        from django.utils import timezone
        
        now = timezone.now()
        return (now - obj.last_seen) < timedelta(minutes=5)


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


class ServerSessionSerializer(serializers.ModelSerializer):
    """Serializer for server sessions."""
    
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    server_name = serializers.CharField(source='server.name', read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ServerSession
        fields = [
            'id', 'staff', 'staff_name', 'server', 'server_name',
            'join_time', 'leave_time', 'duration', 'duration_formatted',
            'is_active', 'steam_id', 'player_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'duration']


class ServerSessionAggregateSerializer(serializers.ModelSerializer):
    """Serializer for session aggregates."""
    
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    server_name = serializers.CharField(source='server.name', read_only=True)
    total_time_formatted = serializers.ReadOnlyField()
    avg_session_time_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = ServerSessionAggregate
        fields = [
            'id', 'staff', 'staff_name', 'server', 'server_name',
            'period_type', 'period_start', 'period_end',
            'total_time', 'total_time_formatted',
            'session_count', 'avg_session_time', 'avg_session_time_formatted',
            'longest_session', 'last_updated'
        ]
        read_only_fields = ['last_updated']


class StaffDetailsSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for staff details page."""
    
    # Basic info from StaffRosterSerializer
    role = serializers.CharField(source='rank', read_only=True)
    role_color = serializers.ReadOnlyField(source='rank_color')
    role_priority = serializers.IntegerField(source='rank_priority', read_only=True)
    username = serializers.CharField(source='name', read_only=True)
    display_name = serializers.CharField(source='name', read_only=True)
    
    # Time tracking statistics
    total_server_time = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    avg_session_duration = serializers.SerializerMethodField()
    last_server_join = serializers.SerializerMethodField()
    
    # Server-specific time
    server_time_breakdown = serializers.SerializerMethodField()
    
    # Counter stats (from counters app)
    sit_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    
    # Recent sessions
    recent_sessions = serializers.SerializerMethodField()
    
    # History timeline
    history_events = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRoster
        fields = [
            'id', 'username', 'display_name', 'role', 'role_color', 'role_priority',
            'steam_id', 'discord_id', 'discord_tag', 'timezone', 'is_active',
            'total_server_time', 'total_sessions', 'avg_session_duration',
            'last_server_join', 'server_time_breakdown',
            'sit_count', 'ticket_count', 'recent_sessions', 'history_events'
        ]
    
    def get_total_server_time(self, obj):
        """Get total time spent on all servers (all time)."""
        from django.db.models import Sum
        total = ServerSession.objects.filter(
            staff=obj.staff,
            leave_time__isnull=False
        ).aggregate(total=Sum('duration'))['total'] or 0
        return total
    
    def get_total_sessions(self, obj):
        """Get total number of sessions."""
        return ServerSession.objects.filter(staff=obj.staff).count()
    
    def get_avg_session_duration(self, obj):
        """Get average session duration."""
        from django.db.models import Avg
        avg = ServerSession.objects.filter(
            staff=obj.staff,
            leave_time__isnull=False
        ).aggregate(avg=Avg('duration'))['avg'] or 0
        return int(avg)
    
    def get_last_server_join(self, obj):
        """Get last time staff member joined a server."""
        last_session = ServerSession.objects.filter(staff=obj.staff).first()
        return last_session.join_time.isoformat() if last_session else None
    
    def get_server_time_breakdown(self, obj):
        """Get time breakdown by server."""
        from apps.servers.models import GameServer
        from django.db.models import Avg, Count, Sum
        
        breakdown = []
        servers = GameServer.objects.filter(is_active=True)
        
        for server in servers:
            stats = ServerSession.objects.filter(
                staff=obj.staff,
                server=server,
                leave_time__isnull=False
            ).aggregate(
                total_time=Sum('duration'),
                session_count=Count('id'),
                avg_duration=Avg('duration')
            )
            
            if stats['session_count'] and stats['session_count'] > 0:
                breakdown.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'total_time': stats['total_time'] or 0,
                    'session_count': stats['session_count'] or 0,
                    'avg_duration': int(stats['avg_duration'] or 0),
                })
        
        return breakdown
    
    def get_sit_count(self, obj):
        """Get total sit count from counters."""
        if not obj.staff.user:
            return 0
        
        from apps.counters.models import Counter
        counter = Counter.objects.filter(
            user=obj.staff.user,
            counter_type='sit',
            period_type='total'
        ).first()
        
        return counter.count if counter else 0
    
    def get_ticket_count(self, obj):
        """Get total ticket count from counters."""
        if not obj.staff.user:
            return 0
        
        from apps.counters.models import Counter
        counter = Counter.objects.filter(
            user=obj.staff.user,
            counter_type='ticket',
            period_type='total'
        ).first()
        
        return counter.count if counter else 0
    
    def get_recent_sessions(self, obj):
        """Get recent server sessions."""
        sessions = ServerSession.objects.filter(staff=obj.staff)[:10]
        return ServerSessionSerializer(sessions, many=True).data
    
    def get_history_events(self, obj):
        """Get staff history timeline events."""
        events = StaffHistoryEvent.objects.filter(staff=obj.staff)[:20]
        return StaffHistoryEventSerializer(events, many=True).data


class StaffHistoryEventSerializer(serializers.ModelSerializer):
    """Serializer for staff history events."""
    
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    event_description = serializers.ReadOnlyField()
    is_promotion = serializers.ReadOnlyField()
    is_demotion = serializers.ReadOnlyField()
    
    old_rank_color = serializers.SerializerMethodField()
    new_rank_color = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffHistoryEvent
        fields = [
            'id', 'staff', 'staff_name', 'event_type', 'event_type_display',
            'old_rank', 'new_rank', 'old_rank_priority', 'new_rank_priority',
            'old_rank_color', 'new_rank_color',
            'event_date', 'notes', 'auto_detected', 'created_by',
            'event_description', 'is_promotion', 'is_demotion', 'created_at'
        ]
        read_only_fields = ['created_at', 'auto_detected']
    
    def get_old_rank_color(self, obj):
        """Get color for old rank."""
        if obj.old_rank:
            return settings.STAFF_ROLE_COLORS.get(obj.old_rank, '#808080')
        return None
    
    def get_new_rank_color(self, obj):
        """Get color for new rank."""
        if obj.new_rank:
            return settings.STAFF_ROLE_COLORS.get(obj.new_rank, '#808080')
        return None
