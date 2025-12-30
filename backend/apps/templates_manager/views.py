from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
import requests

from .models import RefundTemplate, TemplateCategory, ResponseTemplate
from .serializers import (
    RefundTemplateSerializer,
    RefundTemplateCreateSerializer,
    TemplateCategorySerializer,
    ResponseTemplateSerializer,
    SteamProfileSerializer,
)
from apps.accounts.permissions import IsModerator


class RefundTemplateListCreateView(generics.ListCreateAPIView):
    """List and create refund templates."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RefundTemplateCreateSerializer
        return RefundTemplateSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = RefundTemplate.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Non-admins only see their own
        if user.role_priority > 70:  # Below Admin
            queryset = queryset.filter(created_by=user)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RefundTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a refund template."""
    serializer_class = RefundTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role_priority <= 70:  # Admin or above
            return RefundTemplate.objects.all()
        return RefundTemplate.objects.filter(created_by=user)

    def perform_update(self, serializer):
        # If status changed to completed, set resolved info
        if serializer.validated_data.get('status') in ['approved', 'denied', 'completed']:
            serializer.save(
                resolved_by=self.request.user,
                resolved_at=timezone.now()
            )
        else:
            serializer.save()


class TemplateCategoryListView(generics.ListCreateAPIView):
    """List and create template categories."""
    serializer_class = TemplateCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TemplateCategory.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsModerator()]
        return [permissions.IsAuthenticated()]


class ResponseTemplateListCreateView(generics.ListCreateAPIView):
    """List and create response templates."""
    serializer_class = ResponseTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ResponseTemplate.objects.filter(is_active=True)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ResponseTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a response template."""
    serializer_class = ResponseTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]
    queryset = ResponseTemplate.objects.all()


class SteamProfileLookupView(APIView):
    """Look up Steam profile information."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        steam_id = request.data.get('steam_id')
        if not steam_id:
            return Response(
                {'error': 'steam_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile_data = self._lookup_steam_profile(steam_id)
            return Response(profile_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _lookup_steam_profile(self, steam_id):
        """Look up Steam profile using steamidfinder.com."""
        from apps.accounts.pipeline import convert_steam_id_64_to_steam_id
        
        # Convert to SteamID64 if needed
        steam_id_64 = steam_id
        if steam_id.startswith('STEAM_'):
            # Convert STEAM_X:Y:Z to SteamID64
            parts = steam_id.replace('STEAM_', '').split(':')
            if len(parts) == 3:
                y = int(parts[1])
                z = int(parts[2])
                steam_id_64 = str(76561197960265728 + (z * 2) + y)
        
        # Use Steam API if available
        from django.conf import settings
        api_key = settings.SOCIAL_AUTH_STEAM_API_KEY
        
        if api_key:
            response = requests.get(
                f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                params={
                    'key': api_key,
                    'steamids': steam_id_64
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('response', {}).get('players', [])
                if players:
                    player = players[0]
                    steam_id_converted = convert_steam_id_64_to_steam_id(steam_id_64)
                    return {
                        'steam_id': steam_id_converted,
                        'steam_id_64': steam_id_64,
                        'name': player.get('personaname'),
                        'profile_url': player.get('profileurl'),
                        'avatar_url': player.get('avatarfull'),
                        'profile_state': 'public' if player.get('communityvisibilitystate') == 3 else 'private',
                        'real_name': player.get('realname'),
                        'location': player.get('loccountrycode'),
                    }
        
        return {
            'steam_id': steam_id,
            'steam_id_64': steam_id_64,
            'name': None,
            'profile_url': f"https://steamcommunity.com/profiles/{steam_id_64}",
            'avatar_url': None,
            'profile_state': 'unknown',
            'real_name': None,
            'location': None,
        }


class RefundQuestionTemplateView(APIView):
    """Get the standard refund question template."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        template = """Please Send Your:
IGN:
SteamID64:
Server(OG/Normal):
Items Lost:
Reason:
Evidence:
"""
        return Response({'template': template})
