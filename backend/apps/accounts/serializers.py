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
            'staff_left_at', 'last_activity', 'date_joined', 'setup_completed', 'setup_completed_at',
        ]
        read_only_fields = [
            'id', 'role', 'role_priority', 'is_active_staff', 'is_legacy_staff',
            'staff_since', 'staff_left_at',
            'steam_id', 'steam_id_64', 'steam_profile_url', 'steam_avatar',
            'discord_id', 'discord_username', 'discord_avatar',
            'date_joined', 'last_activity', 'setup_completed_at',
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


class SetupWizardSerializer(serializers.Serializer):
    """Serializer for completing the first-time setup wizard."""
    
    timezone = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(required=False, write_only=True, min_length=8, allow_blank=True)
    auto_sit_detection_enabled = serializers.BooleanField(required=False, default=True)
    auto_recording_enabled = serializers.BooleanField(required=False, default=True)
    
    def validate_timezone(self, value):
        if value not in pytz.common_timezones:
            raise serializers.ValidationError('Invalid timezone.')
        return value
    
    def update(self, instance, validated_data):
        """Update user with setup wizard data."""
        from django.utils import timezone as django_timezone

        # Update timezone
        instance.timezone = validated_data.get('timezone', instance.timezone)
        
        # Update email if provided
        if validated_data.get('email'):
            instance.email = validated_data['email']
        
        # Update password if provided
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        
        # Mark setup as completed
        instance.setup_completed = True
        instance.setup_completed_at = django_timezone.now()
        
        instance.save()
        
        # Create or update sit preferences
        from apps.counters.models import UserSitPreferences
        preferences, created = UserSitPreferences.objects.get_or_create(user=instance)
        
        # Update auto detection and recording based on wizard choices
        preferences.ocr_enabled = validated_data.get('auto_sit_detection_enabled', True)
        preferences.recording_enabled = validated_data.get('auto_recording_enabled', True)
        preferences.auto_start_recording = validated_data.get('auto_recording_enabled', True)
        preferences.auto_stop_recording = validated_data.get('auto_recording_enabled', True)
        preferences.save()
        
        return instance


class SocialLinkSerializer(serializers.Serializer):
    """Serializer for social account linking status."""
    
    steam_linked = serializers.BooleanField(read_only=True)
    steam_id = serializers.CharField(read_only=True, allow_null=True)
    discord_linked = serializers.BooleanField(read_only=True)
    discord_id = serializers.CharField(read_only=True, allow_null=True)
    discord_username = serializers.CharField(read_only=True, allow_null=True)
