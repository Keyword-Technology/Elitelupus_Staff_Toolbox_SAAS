import pytz
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    role_color = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'avatar_url',
            'role', 'role_priority', 'role_color',
            'steam_id', 'steam_id_64', 'steam_profile_url', 'steam_avatar',
            'discord_id', 'discord_username', 'discord_avatar',
            'timezone', 'use_24_hour_time', 'is_active_staff', 'is_legacy_staff', 'staff_since', 
            'staff_left_at', 'last_activity', 'date_joined',
        ]
        read_only_fields = [
            'id', 'role', 'role_priority', 'is_active_staff', 'is_legacy_staff',
            'staff_since', 'staff_left_at',
            'steam_id', 'steam_id_64', 'steam_profile_url', 'steam_avatar',
            'discord_id', 'discord_username', 'discord_avatar',
            'date_joined', 'last_activity',
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['display_name', 'email', 'timezone', 'use_24_hour_time']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'display_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional claims."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['display_name'] = user.display_name or user.username
        token['role'] = user.role
        token['role_priority'] = user.role_priority
        token['steam_id'] = user.steam_id
        token['discord_id'] = user.discord_id
        
        return token


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs


class TimezoneSerializer(serializers.Serializer):
    """Serializer for available timezones."""
    
    timezones = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )

    def to_representation(self, instance):
        return {
            'timezones': pytz.common_timezones
        }


class SocialLinkSerializer(serializers.Serializer):
    """Serializer for social account linking status."""
    
    steam_linked = serializers.BooleanField(read_only=True)
    steam_id = serializers.CharField(read_only=True, allow_null=True)
    discord_linked = serializers.BooleanField(read_only=True)
    discord_id = serializers.CharField(read_only=True, allow_null=True)
    discord_username = serializers.CharField(read_only=True, allow_null=True)
