from rest_framework import serializers

from .models import Feature, FeatureComment


class FeatureCommentSerializer(serializers.ModelSerializer):
    """Serializer for feature comments."""
    
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.CharField(source='author.display_name', read_only=True)
    author_avatar = serializers.URLField(source='author.avatar_url', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    author_role_color = serializers.SerializerMethodField()
    is_own_comment = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureComment
        fields = [
            'id',
            'feature',
            'author',
            'author_username',
            'author_display_name',
            'author_avatar',
            'author_role',
            'author_role_color',
            'content',
            'created_at',
            'updated_at',
            'is_own_comment',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_author_role_color(self, obj):
        from apps.staff.models import StaffMember
        role_colors = {
            'SYSADMIN': '#FF0000',
            'Manager': '#990000',
            'Staff Manager': '#F04000',
            'Assistant Staff Manager': '#8900F0',
            'Meta Manager': '#8900F0',
            'Event Manager': '#8900F0',
            'Senior Admin': '#d207d3',
            'Admin': '#FA1E8A',
            'Senior Moderator': '#15c000',
            'Moderator': '#4a86e8',
            'Senior Operator': '#38761d',
            'Operator': '#93c47d',
            'T-Staff': '#b6d7a8',
            'User': '#9e9e9e',
        }
        return role_colors.get(obj.author.role, '#9e9e9e')
    
    def get_is_own_comment(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False


class FeatureCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    
    class Meta:
        model = FeatureComment
        fields = ['content']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['feature'] = self.context['feature']
        return super().create(validated_data)


class FeatureListSerializer(serializers.ModelSerializer):
    """Serializer for listing features."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Feature
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
            'target_date',
            'order',
            'comment_count',
        ]


class FeatureDetailSerializer(serializers.ModelSerializer):
    """Serializer for feature detail with comments."""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    comments = FeatureCommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Feature
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
            'target_date',
            'order',
            'comment_count',
            'comments',
        ]


class FeatureWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating features (SYSADMIN only)."""
    
    class Meta:
        model = Feature
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'target_date',
            'order',
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
