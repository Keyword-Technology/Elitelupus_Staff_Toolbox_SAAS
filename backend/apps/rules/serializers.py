from rest_framework import serializers

from .models import JobAction, Rule, RuleCategory


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for individual rules."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Rule
        fields = ['id', 'code', 'title', 'content', 'order', 'is_active', 'category', 'category_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class RuleWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rules."""
    
    class Meta:
        model = Rule
        fields = ['id', 'category', 'code', 'title', 'content', 'order', 'is_active']


class RuleCategorySerializer(serializers.ModelSerializer):
    """Serializer for rule categories with nested rules."""
    
    rules = RuleSerializer(many=True, read_only=True)
    rule_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'description', 'order', 'icon', 'is_active', 'rules', 'rule_count']
    
    def get_rule_count(self, obj):
        return obj.rules.filter(is_active=True).count()


class RuleCategoryWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rule categories."""
    
    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'description', 'order', 'icon', 'is_active']


class RuleCategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for category listing."""
    
    rule_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'description', 'order', 'icon', 'rule_count']
    
    def get_rule_count(self, obj):
        return obj.rules.filter(is_active=True).count()


class JobActionSerializer(serializers.ModelSerializer):
    """Serializer for job actions."""
    
    class Meta:
        model = JobAction
        fields = '__all__'


class JobActionWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating job actions."""
    
    class Meta:
        model = JobAction
        fields = [
            'id', 'job_name', 'category',
            'can_raid', 'raid_note',
            'can_steal', 'steal_note',
            'can_mug', 'mug_note',
            'can_kidnap', 'kidnap_note',
            'can_base', 'base_note',
            'can_have_printers', 'printers_note',
            'additional_notes', 'order', 'is_active'
        ]


class JobActionSummarySerializer(serializers.Serializer):
    """Summary serializer for job action lookup."""
    
    job_name = serializers.CharField()
    can_raid = serializers.BooleanField()
    can_steal = serializers.BooleanField()
    can_mug = serializers.BooleanField()
    can_kidnap = serializers.BooleanField()
    can_base = serializers.BooleanField()
    can_have_printers = serializers.BooleanField()
