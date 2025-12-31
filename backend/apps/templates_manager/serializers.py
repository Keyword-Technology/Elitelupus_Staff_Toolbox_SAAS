from rest_framework import serializers

from .models import (BanExtensionTemplate, PlayerReportTemplate,
                     RefundTemplate, ResponseTemplate,
                     StaffApplicationResponse, SteamProfileHistory,
                     SteamProfileSearch, TemplateCategory, TemplateComment)


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


class BanExtensionTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ban extension templates."""
    
    submitted_by_name = serializers.CharField(source='submitted_by.display_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.display_name', read_only=True, allow_null=True)
    is_active_ban = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BanExtensionTemplate
        fields = '__all__'
        read_only_fields = ['submitted_by', 'created_at', 'updated_at']


class PlayerReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for player report templates."""
    
    handled_by_name = serializers.CharField(source='handled_by.display_name', read_only=True)
    
    class Meta:
        model = PlayerReportTemplate
        fields = '__all__'
        read_only_fields = ['handled_by', 'created_at', 'updated_at']


class StaffApplicationResponseSerializer(serializers.ModelSerializer):
    """Serializer for staff application responses."""
    
    reviewed_by_name = serializers.CharField(source='reviewed_by.display_name', read_only=True)
    rating_stars = serializers.CharField(read_only=True)
    
    class Meta:
        model = StaffApplicationResponse
        fields = '__all__'
        read_only_fields = ['reviewed_by', 'created_at', 'updated_at']


class TemplateCommentSerializer(serializers.ModelSerializer):
    """Serializer for template comments."""
    
    author_name = serializers.CharField(source='author.display_name', read_only=True)
    
    class Meta:
        model = TemplateComment
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at']

