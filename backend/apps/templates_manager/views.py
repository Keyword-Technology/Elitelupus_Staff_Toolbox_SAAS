import requests
from apps.accounts.permissions import IsModerator
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (RefundTemplate, ResponseTemplate, SteamProfileBookmark,
                     SteamProfileHistory, SteamProfileNote, SteamProfileSearch,
                     TemplateCategory)
from .serializers import (RefundTemplateCreateSerializer,
                          RefundTemplateSerializer, ResponseTemplateSerializer,
                          SteamProfileBookmarkCreateSerializer,
                          SteamProfileBookmarkSerializer,
                          SteamProfileHistorySerializer,
                          SteamProfileNoteCreateSerializer,
                          SteamProfileNoteSerializer,
                          SteamProfileSearchSerializer, SteamProfileSerializer,
                          TemplateCategorySerializer)
from .services import SteamLookupService


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
    """Look up Steam profile information with tracking and history."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        steam_id = request.data.get('steam_id')
        if not steam_id:
            return Response(
                {'error': 'steam_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use the enhanced lookup service
            service = SteamLookupService()
            profile_data = service.lookup_profile(steam_id, user=request.user)
            
            serializer = SteamProfileSerializer(data=profile_data)
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SteamProfileSearchListView(generics.ListAPIView):
    """List all Steam profile searches with statistics."""
    serializer_class = SteamProfileSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SteamProfileSearch.objects.all()
        
        # Filter by steam_id_64 if provided
        steam_id_64 = self.request.query_params.get('steam_id_64')
        if steam_id_64:
            queryset = queryset.filter(steam_id_64=steam_id_64)
        
        # Order by most searched
        order_by = self.request.query_params.get('order_by', '-search_count')
        queryset = queryset.order_by(order_by)
        
        return queryset[:100]  # Limit to top 100


class SteamProfileSearchDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific Steam profile search."""
    serializer_class = SteamProfileSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SteamProfileSearch.objects.all()
    lookup_field = 'steam_id_64'


class SteamProfileHistoryListView(generics.ListAPIView):
    """List search history for a Steam profile."""
    serializer_class = SteamProfileHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        steam_id_64 = self.request.query_params.get('steam_id_64')
        if not steam_id_64:
            return SteamProfileHistory.objects.none()
        
        try:
            search = SteamProfileSearch.objects.get(steam_id_64=steam_id_64)
            return search.history.all()[:50]  # Last 50 searches
        except SteamProfileSearch.DoesNotExist:
            return SteamProfileHistory.objects.none()


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


class SteamProfileNoteListCreateView(generics.ListCreateAPIView):
    """List and create notes for a Steam profile."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SteamProfileNoteCreateSerializer
        return SteamProfileNoteSerializer
    
    def get_queryset(self):
        steam_id_64 = self.request.query_params.get('steam_id_64')
        if not steam_id_64:
            return SteamProfileNote.objects.none()
        
        try:
            steam_profile = SteamProfileSearch.objects.get(steam_id_64=steam_id_64)
            return steam_profile.notes.all()
        except SteamProfileSearch.DoesNotExist:
            return SteamProfileNote.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SteamProfileNoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a Steam profile note."""
    serializer_class = SteamProfileNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SteamProfileNote.objects.all()
    
    def perform_update(self, serializer):
        # If marking as resolved, set resolved info
        if not serializer.instance.resolved_at and not serializer.validated_data.get('is_active', True):
            serializer.save(
                resolved_by=self.request.user,
                resolved_at=timezone.now()
            )
        else:
            serializer.save()


class SteamProfileBookmarkListCreateView(generics.ListCreateAPIView):
    """List and create Steam profile bookmarks."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SteamProfileBookmarkCreateSerializer
        return SteamProfileBookmarkSerializer
    
    def get_queryset(self):
        # Only return bookmarks for the current user
        return SteamProfileBookmark.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SteamProfileBookmarkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a Steam profile bookmark."""
    serializer_class = SteamProfileBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow users to manage their own bookmarks
        return SteamProfileBookmark.objects.filter(user=self.request.user)

