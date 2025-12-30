from rest_framework import serializers
from .models import RuleCategory, Rule, JobAction


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for individual rules."""
    
    class Meta:
        model = Rule
        fields = ['id', 'code', 'title', 'content', 'order', 'is_active']


class RuleCategorySerializer(serializers.ModelSerializer):
    """Serializer for rule categories with nested rules."""
    
    rules = RuleSerializer(many=True, read_only=True)
    rule_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'description', 'order', 'icon', 'is_active', 'rules', 'rule_count']
    
    def get_rule_count(self, obj):
        return obj.rules.filter(is_active=True).count()


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


class JobActionSummarySerializer(serializers.Serializer):
    """Summary serializer for job action lookup."""
    
    job_name = serializers.CharField()
    can_raid = serializers.BooleanField()
    can_steal = serializers.BooleanField()
    can_mug = serializers.BooleanField()
    can_kidnap = serializers.BooleanField()
    can_base = serializers.BooleanField()
    can_have_printers = serializers.BooleanField()
