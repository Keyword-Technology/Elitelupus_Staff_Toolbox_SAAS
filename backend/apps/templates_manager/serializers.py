from rest_framework import serializers
from .models import RefundTemplate, TemplateCategory, ResponseTemplate


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
    """Serializer for Steam profile data."""
    
    steam_id = serializers.CharField()
    steam_id_3 = serializers.CharField(allow_null=True)
    steam_id_64 = serializers.CharField()
    name = serializers.CharField(allow_null=True)
    profile_url = serializers.URLField(allow_null=True)
    avatar_url = serializers.URLField(allow_null=True)
    profile_state = serializers.CharField(allow_null=True)
    real_name = serializers.CharField(allow_null=True)
    location = serializers.CharField(allow_null=True)
