from rest_framework import serializers

from .models import (BanExtensionTemplate, PlayerReportTemplate,
                     RefundTemplate, ResponseTemplate,
                     StaffApplicationResponse, SteamProfileBookmark,
                     SteamProfileHistory, SteamProfileNote, SteamProfileSearch,
                     TemplateCategory, TemplateComment)


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
    
    # Accept frontend field names (for backward compatibility)
    items = serializers.CharField(write_only=True, required=False, allow_blank=True)
    proof = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Make server and ticket_number optional
    server = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ticket_number = serializers.CharField(required=False, allow_blank=True, max_length=50)
    
    class Meta:
        model = RefundTemplate
        fields = [
            'ticket_number', 'player_ign', 'steam_id', 'steam_id_64',
            'server', 'items_lost', 'reason', 'evidence', 'items', 'proof'
        ]
        extra_kwargs = {
            'evidence': {'required': False, 'allow_blank': True},
            'steam_id_64': {'required': False, 'allow_blank': True},
            'items_lost': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, data):
        """Map frontend field names to backend field names."""
        # Map 'items' to 'items_lost'
        if 'items' in data:
            data['items_lost'] = data.pop('items')
        
        # Map 'proof' to 'evidence'
        if 'proof' in data:
            data['evidence'] = data.pop('proof')
        
        # Generate ticket number if not provided
        if not data.get('ticket_number'):
            import uuid
            data['ticket_number'] = f"REF-{uuid.uuid4().hex[:8].upper()}"
        
        # Ensure items_lost has a value
        if not data.get('items_lost'):
            data['items_lost'] = 'Not specified'
        
        return data


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
    
    id = serializers.IntegerField(required=False)
    steam_id = serializers.CharField()
    steam_id_64 = serializers.CharField()
    
    profile = serializers.DictField()
    bans = serializers.DictField()
    search_stats = serializers.DictField()
    changes = serializers.DictField()
    related_templates = serializers.DictField()  # Changed from ListField to DictField
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


class SteamProfileNoteSerializer(serializers.ModelSerializer):
    """Serializer for Steam profile notes."""
    
    author_name = serializers.CharField(source='author.display_name', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.display_name', read_only=True, allow_null=True)
    warning_count = serializers.IntegerField(read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = SteamProfileNote
        fields = '__all__'
        read_only_fields = ['author', 'created_at', 'updated_at', 'resolved_by', 'resolved_at']


class SteamProfileNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Steam profile notes."""
    
    class Meta:
        model = SteamProfileNote
        fields = [
            'steam_profile', 'note_type', 'title', 'content',
            'severity', 'server', 'expires_at'
        ]


class SteamProfileBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for Steam profile bookmarks."""
    
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    steam_profile_data = serializers.SerializerMethodField()
    
    class Meta:
        model = SteamProfileBookmark
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_steam_profile_data(self, obj):
        """Include basic Steam profile data."""
        return {
            'steam_id_64': obj.steam_profile.steam_id_64,
            'persona_name': obj.steam_profile.persona_name,
            'avatar_url': obj.steam_profile.avatar_url,
            'profile_url': obj.steam_profile.profile_url,
            'vac_bans': obj.steam_profile.vac_bans,
            'game_bans': obj.steam_profile.game_bans,
            'last_searched_at': obj.steam_profile.last_searched_at,
            'search_count': obj.steam_profile.search_count,
        }


class SteamProfileBookmarkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Steam profile bookmarks."""
    
    steam_id_64 = serializers.CharField(write_only=True)
    
    class Meta:
        model = SteamProfileBookmark
        fields = ['steam_id_64', 'note', 'tags', 'is_pinned']
    
    def create(self, validated_data):
        steam_id_64 = validated_data.pop('steam_id_64')
        user = self.context['request'].user
        
        # Get or create the steam profile search
        steam_profile, created = SteamProfileSearch.objects.get_or_create(
            steam_id_64=steam_id_64,
            defaults={'last_searched_by': user}
        )
        
        # Create the bookmark
        bookmark, created = SteamProfileBookmark.objects.update_or_create(
            user=user,
            steam_profile=steam_profile,
            defaults=validated_data
        )
        
        return bookmark


