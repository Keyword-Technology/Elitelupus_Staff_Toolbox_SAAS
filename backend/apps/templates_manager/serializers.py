from rest_framework import serializers

from .models import (RefundTemplate, ResponseTemplate, SteamProfileHistory,
                     SteamProfileSearch, TemplateCategory)


class SteamProfileSearchSerializer(serializers.ModelSerializer):
    """Serializer for Steam profile search records."""
    
    last_searched_by_name = serializers.CharField(
        source='last_searched_by.username', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = SteamProfileSearch
        fields = '__all__'
        read_only_fields = [
            'search_count', 'first_searched_at', 'last_searched_at',
            'last_searched_by'
        ]


class SteamProfileHistorySerializer(serializers.ModelSerializer):
    """Serializer for Steam profile history entries."""
    
    searched_by_name = serializers.CharField(
        source='searched_by.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = SteamProfileHistory
        fields = '__all__'
        read_only_fields = ['searched_at']


class RefundTemplateSerializer(serializers.ModelSerializer):
    """Serializer for refund templates."""
    
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.display_name', read_only=True, allow_null=True)
    
    class Meta:
        model = RefundTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class RefundTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating refund templates."""
    
    class Meta:
        model = RefundTemplate
        fields = [
            'ticket_number', 'player_ign', 'steam_id', 'steam_id_64',
            'server', 'items_lost', 'reason', 'evidence'
        ]


class TemplateCategorySerializer(serializers.ModelSerializer):
    """Serializer for template categories."""
    
    template_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateCategory
        fields = '__all__'
    
    def get_template_count(self, obj):
        return obj.templates.filter(is_active=True).count()


class ResponseTemplateSerializer(serializers.ModelSerializer):
    """Serializer for response templates."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ResponseTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class SteamProfileLookupSerializer(serializers.Serializer):
    """Serializer for Steam profile lookup."""
    
    steam_id = serializers.CharField()


class SteamProfileSerializer(serializers.Serializer):
    """Serializer for enhanced Steam profile data with tracking."""
    
    steam_id = serializers.CharField()
    steam_id_64 = serializers.CharField()
    
    profile = serializers.DictField()
    bans = serializers.DictField()
    search_stats = serializers.DictField()
    changes = serializers.DictField()
    related_templates = serializers.ListField()
    search_history = serializers.ListField()
