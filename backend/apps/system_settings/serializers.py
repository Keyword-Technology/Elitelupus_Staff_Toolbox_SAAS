from rest_framework import serializers
from .models import SystemSetting, ManagedServer, SettingAuditLog


class SystemSettingSerializer(serializers.ModelSerializer):
    """Serializer for system settings."""
    
    display_value = serializers.ReadOnlyField()
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = SystemSetting
        fields = [
            'id', 'key', 'value', 'display_value', 'setting_type', 'category',
            'description', 'is_sensitive', 'is_active', 'created_at', 'updated_at',
            'updated_by', 'updated_by_username'
        ]
        read_only_fields = ['created_at', 'updated_at', 'updated_by']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Use display_value instead of actual value for sensitive settings
        if instance.is_sensitive:
            data['value'] = data['display_value']
        return data


class SystemSettingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating system settings."""
    
    class Meta:
        model = SystemSetting
        fields = [
            'key', 'value', 'setting_type', 'category',
            'description', 'is_sensitive', 'is_active'
        ]


class ManagedServerSerializer(serializers.ModelSerializer):
    """Serializer for managed servers."""
    
    address = serializers.ReadOnlyField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ManagedServer
        fields = [
            'id', 'name', 'ip_address', 'port', 'description', 'is_active',
            'display_order', 'query_port', 'address', 'created_at', 'updated_at',
            'created_by', 'created_by_username'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
        extra_kwargs = {
            'rcon_password': {'write_only': True}
        }


class ManagedServerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating managed servers."""
    
    class Meta:
        model = ManagedServer
        fields = [
            'name', 'ip_address', 'port', 'description', 'is_active',
            'display_order', 'rcon_password', 'query_port'
        ]


class SettingAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for setting audit logs."""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    setting_key = serializers.CharField(source='setting.key', read_only=True)
    
    class Meta:
        model = SettingAuditLog
        fields = [
            'id', 'setting', 'setting_key', 'user', 'user_username',
            'old_value', 'new_value', 'changed_at', 'ip_address'
        ]
        read_only_fields = ['__all__']


class EnvironmentVariableSerializer(serializers.Serializer):
    """Serializer for displaying environment variables and their overridable status."""
    
    key = serializers.CharField()
    env_value = serializers.CharField(allow_null=True)
    override_value = serializers.CharField(allow_null=True)
    effective_value = serializers.CharField()
    is_overridden = serializers.BooleanField()
    is_sensitive = serializers.BooleanField()
    category = serializers.CharField()
    description = serializers.CharField()
