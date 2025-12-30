import os

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ManagedServer, SettingAuditLog, SystemSetting
from .serializers import (EnvironmentVariableSerializer,
                          ManagedServerCreateSerializer,
                          ManagedServerSerializer, SettingAuditLogSerializer,
                          SystemSettingCreateSerializer,
                          SystemSettingSerializer)


class IsAdminUser(permissions.BasePermission):
    """Permission check for admin users (role priority <= 70)."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role_priority <= 70 or request.user.is_superuser


# Environment variables that can be configured
CONFIGURABLE_ENV_VARS = [
    {
        'key': 'STEAM_API_KEY',
        'category': 'api_keys',
        'description': 'Steam Web API key for player lookups',
        'is_sensitive': True,
    },
    {
        'key': 'DISCORD_CLIENT_ID',
        'category': 'api_keys',
        'description': 'Discord OAuth application client ID',
        'is_sensitive': False,
    },
    {
        'key': 'DISCORD_CLIENT_SECRET',
        'category': 'api_keys',
        'description': 'Discord OAuth application client secret',
        'is_sensitive': True,
    },
    {
        'key': 'GOOGLE_SHEETS_ID',
        'category': 'external',
        'description': 'Google Sheets ID for staff roster sync',
        'is_sensitive': False,
    },
    {
        'key': 'FRONTEND_URL',
        'category': 'general',
        'description': 'URL of the frontend application',
        'is_sensitive': False,
    },
    {
        'key': 'DEBUG',
        'category': 'general',
        'description': 'Enable debug mode (True/False)',
        'is_sensitive': False,
    },
    {
        'key': 'ALLOWED_HOSTS',
        'category': 'general',
        'description': 'Comma-separated list of allowed hostnames',
        'is_sensitive': False,
    },
]


class EnvironmentVariableListView(APIView):
    """List all configurable environment variables with their current and override values."""
    
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        result = []
        
        for var_config in CONFIGURABLE_ENV_VARS:
            key = var_config['key']
            env_value = os.getenv(key, '')
            
            # Check for override in database
            override = SystemSetting.objects.filter(
                key=key, 
                is_active=True
            ).first()
            
            override_value = override.value if override else None
            effective_value = override_value if override_value else env_value
            
            # Mask sensitive values
            if var_config['is_sensitive']:
                if env_value:
                    env_value = '*' * 8 + env_value[-4:] if len(env_value) > 4 else '****'
                if override_value:
                    override_value = '*' * 8 + override_value[-4:] if len(override_value) > 4 else '****'
                if effective_value:
                    effective_value = '*' * 8 + effective_value[-4:] if len(effective_value) > 4 else '****'
            
            result.append({
                'key': key,
                'env_value': env_value or None,
                'override_value': override_value,
                'effective_value': effective_value,
                'is_overridden': override is not None,
                'is_sensitive': var_config['is_sensitive'],
                'category': var_config['category'],
                'description': var_config['description'],
            })
        
        return Response(result)


class EnvironmentVariableUpdateView(APIView):
    """Update an environment variable override."""
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, key):
        # Validate key is in configurable list
        var_config = next((v for v in CONFIGURABLE_ENV_VARS if v['key'] == key), None)
        if not var_config:
            return Response(
                {'error': f'Environment variable {key} is not configurable'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        value = request.data.get('value', '')
        
        if value:
            # Create or update the override
            setting, created = SystemSetting.objects.update_or_create(
                key=key,
                defaults={
                    'value': value,
                    'setting_type': 'string',
                    'category': var_config['category'],
                    'description': var_config['description'],
                    'is_sensitive': var_config['is_sensitive'],
                    'is_active': True,
                    'updated_by': request.user,
                }
            )
            
            # Create audit log
            SettingAuditLog.objects.create(
                setting=setting,
                user=request.user,
                old_value='' if created else 'changed',
                new_value=value if not var_config['is_sensitive'] else '****',
                ip_address=self._get_client_ip(request),
            )
            
            return Response({
                'message': f'Override for {key} {"created" if created else "updated"}',
                'key': key,
            })
        else:
            # Remove the override
            deleted, _ = SystemSetting.objects.filter(key=key).delete()
            if deleted:
                return Response({'message': f'Override for {key} removed'})
            return Response({'message': f'No override existed for {key}'})
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class SystemSettingListView(generics.ListCreateAPIView):
    """List all system settings or create a new one."""
    
    permission_classes = [IsAdminUser]
    queryset = SystemSetting.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SystemSettingCreateSerializer
        return SystemSettingSerializer
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)


class SystemSettingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a system setting."""
    
    permission_classes = [IsAdminUser]
    queryset = SystemSetting.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SystemSettingCreateSerializer
        return SystemSettingSerializer
    
    def perform_update(self, serializer):
        instance = self.get_object()
        old_value = instance.value
        
        serializer.save(updated_by=self.request.user)
        
        # Create audit log
        SettingAuditLog.objects.create(
            setting=instance,
            user=self.request.user,
            old_value=old_value if not instance.is_sensitive else '****',
            new_value=serializer.validated_data.get('value', '') if not instance.is_sensitive else '****',
            ip_address=self._get_client_ip(),
        )
    
    def _get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


# Managed Server Views

class ManagedServerListView(generics.ListCreateAPIView):
    """List all managed servers or create a new one."""
    
    permission_classes = [IsAdminUser]
    queryset = ManagedServer.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManagedServerCreateSerializer
        return ManagedServerSerializer
    
    def perform_create(self, serializer):
        server = serializer.save(created_by=self.request.user)
        # Sync to GameServer model
        server.sync_to_game_server()


class ManagedServerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a managed server."""
    
    permission_classes = [IsAdminUser]
    queryset = ManagedServer.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ManagedServerCreateSerializer
        return ManagedServerSerializer
    
    def perform_update(self, serializer):
        server = serializer.save()
        # Sync changes to GameServer model
        server.sync_to_game_server()
    
    def perform_destroy(self, instance):
        # Optionally deactivate the GameServer instead of deleting
        from apps.servers.models import GameServer
        GameServer.objects.filter(
            ip_address=instance.ip_address,
            port=instance.port
        ).update(is_active=False)
        instance.delete()


class SyncManagedServersView(APIView):
    """Sync all managed servers to the GameServer model."""
    
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        servers = ManagedServer.objects.filter(is_active=True)
        synced = []
        
        for server in servers:
            game_server, created = server.sync_to_game_server()
            synced.append({
                'name': server.name,
                'address': server.address,
                'created': created,
            })
        
        return Response({
            'message': f'Synced {len(synced)} servers',
            'servers': synced,
        })


class SettingAuditLogListView(generics.ListAPIView):
    """List audit logs for system settings."""
    
    permission_classes = [IsAdminUser]
    serializer_class = SettingAuditLogSerializer
    queryset = SettingAuditLog.objects.all()[:100]
