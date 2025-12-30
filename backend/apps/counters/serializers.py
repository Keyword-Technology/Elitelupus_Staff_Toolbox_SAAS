from rest_framework import serializers
from .models import Counter, CounterHistory, CounterSnapshot


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
    
    class Meta:
        model = CounterHistory
        fields = '__all__'


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
