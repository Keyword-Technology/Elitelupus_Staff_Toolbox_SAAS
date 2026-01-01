from rest_framework import serializers

from .models import (Counter, CounterHistory, CounterSnapshot, Sit, SitNote,
                     UserSitPreferences)


class CounterSerializer(serializers.ModelSerializer):
    """Serializer for counter data."""
    
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Counter
        fields = [
            'id', 'user', 'username', 'user_display_name',
            'counter_type', 'count', 'period_type', 'period_start',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class CounterUpdateSerializer(serializers.Serializer):
    """Serializer for counter updates."""
    
    action = serializers.ChoiceField(choices=['increment', 'decrement', 'set', 'reset'])
    value = serializers.IntegerField(required=False, default=1)
    note = serializers.CharField(required=False, allow_blank=True, default='')


class CounterHistorySerializer(serializers.ModelSerializer):
    """Serializer for counter history."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    value = serializers.SerializerMethodField()
    
    class Meta:
        model = CounterHistory
        fields = '__all__'
    
    def get_value(self, obj):
        """Calculate the change value from old_value to new_value."""
        return abs(obj.new_value - obj.old_value)


class CounterSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for counter snapshots."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)
    
    class Meta:
        model = CounterSnapshot
        fields = '__all__'


class CounterStatsSerializer(serializers.Serializer):
    """Serializer for counter statistics."""
    
    total_sits = serializers.IntegerField()
    total_tickets = serializers.IntegerField()
    today_sits = serializers.IntegerField()
    today_tickets = serializers.IntegerField()
    weekly_sits = serializers.IntegerField()
    weekly_tickets = serializers.IntegerField()


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for leaderboard entries."""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.URLField(allow_null=True)
    role = serializers.CharField()
    role_color = serializers.CharField()
    sit_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


# ============================================================================
# SIT RECORDING SYSTEM SERIALIZERS
# ============================================================================

class SitNoteSerializer(serializers.ModelSerializer):
    """Serializer for sit notes."""
    
    class Meta:
        model = SitNote
        fields = [
            'id', 'sit', 'note_type', 'content',
            'steam_id', 'steam_profile_url', 'steam_persona_name',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SitNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sit notes."""
    
    class Meta:
        model = SitNote
        fields = ['note_type', 'content', 'steam_id', 'steam_profile_url', 'steam_persona_name']


class SitSerializer(serializers.ModelSerializer):
    """Serializer for sit data."""
    
    staff_username = serializers.CharField(source='staff.username', read_only=True)
    staff_display_name = serializers.CharField(source='staff.display_name', read_only=True)
    notes = SitNoteSerializer(many=True, read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    recording_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Sit
        fields = [
            'id', 'staff', 'staff_username', 'staff_display_name',
            'reporter_name', 'reported_player', 'report_type', 'report_reason',
            'started_at', 'ended_at', 'duration_seconds', 'duration_formatted',
            'outcome', 'outcome_notes', 'ban_duration',
            'player_rating', 'player_rating_credits',
            'detection_method',
            'has_recording', 'recording_url', 'thumbnail_url',
            'recording_size_bytes', 'recording_duration_seconds',
            'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'staff', 'duration_seconds', 'has_recording',
            'recording_size_bytes', 'recording_duration_seconds',
            'created_at', 'updated_at'
        ]
    
    def get_duration_formatted(self, obj):
        """Format duration as MM:SS or HH:MM:SS."""
        if not obj.duration_seconds:
            return None
        
        hours, remainder = divmod(obj.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    def get_recording_url(self, obj):
        """Get the recording file URL."""
        if obj.recording_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.recording_file.url)
            return obj.recording_file.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Get the thumbnail URL."""
        if obj.recording_thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.recording_thumbnail.url)
            return obj.recording_thumbnail.url
        return None


class SitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new sit."""
    
    class Meta:
        model = Sit
        fields = [
            'reporter_name', 'reported_player', 'report_type', 'report_reason',
            'started_at', 'detection_method'
        ]


class SitUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating/completing a sit."""
    
    class Meta:
        model = Sit
        fields = [
            'reporter_name', 'reported_player', 'report_type', 'report_reason',
            'ended_at', 'outcome', 'outcome_notes', 'ban_duration',
            'player_rating', 'player_rating_credits'
        ]


class SitRecordingUploadSerializer(serializers.Serializer):
    """Serializer for uploading sit recording."""
    
    recording = serializers.FileField()
    thumbnail = serializers.ImageField(required=False)


class SitListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for sit listing."""
    
    staff_username = serializers.CharField(source='staff.username', read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Sit
        fields = [
            'id', 'staff_username', 'reporter_name', 'reported_player',
            'report_type', 'started_at', 'ended_at', 'duration_formatted',
            'outcome', 'player_rating', 'has_recording', 'detection_method'
        ]
    
    def get_duration_formatted(self, obj):
        if not obj.duration_seconds:
            return None
        minutes, seconds = divmod(obj.duration_seconds, 60)
        return f"{minutes}:{seconds:02d}"


class UserSitPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user sit preferences."""
    
    class Meta:
        model = UserSitPreferences
        fields = [
            'recording_enabled', 'ocr_enabled',
            'auto_start_recording', 'auto_stop_recording',
            'ocr_scan_interval_ms', 'ocr_popup_region_enabled', 'ocr_chat_region_enabled',
            'video_quality', 'max_recording_minutes',
            'show_recording_preview', 'confirm_before_start',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SitStatsSerializer(serializers.Serializer):
    """Serializer for sit statistics."""
    
    total_sits = serializers.IntegerField()
    today_sits = serializers.IntegerField()
    weekly_sits = serializers.IntegerField()
    monthly_sits = serializers.IntegerField()
    sits_with_recording = serializers.IntegerField()
    average_duration_seconds = serializers.FloatField()
    average_rating = serializers.FloatField(allow_null=True)
    outcome_breakdown = serializers.DictField()
    detection_method_breakdown = serializers.DictField()
