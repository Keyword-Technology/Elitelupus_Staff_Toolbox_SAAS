from apps.accounts.permissions import IsSysAdmin
from django.db.models import Case, Count, IntegerField, When
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Feature, FeatureComment
from .serializers import (FeatureCommentCreateSerializer,
                          FeatureCommentSerializer, FeatureDetailSerializer,
                          FeatureListSerializer, FeatureWriteSerializer)

# ==================== PUBLIC VIEWS (Authenticated users) ====================

class FeatureListView(generics.ListAPIView):
    """List all features. All authenticated users can view."""
    
    serializer_class = FeatureListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Define priority ordering: critical=1, high=2, medium=3, low=4
        priority_order = Case(
            When(priority='critical', then=1),
            When(priority='high', then=2),
            When(priority='medium', then=3),
            When(priority='low', then=4),
            output_field=IntegerField(),
        )
        
        queryset = Feature.objects.annotate(
            comment_count=Count('comments'),
            priority_order=priority_order
        ).select_related('created_by').order_by('priority_order', 'order', '-created_at')
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class FeatureDetailView(generics.RetrieveAPIView):
    """Get feature details with comments. All authenticated users can view."""
    
    serializer_class = FeatureDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Feature.objects.annotate(
            comment_count=Count('comments')
        ).prefetch_related('comments__author').select_related('created_by')


class FeatureCommentListCreateView(generics.ListCreateAPIView):
    """List and create comments on a feature."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FeatureCommentCreateSerializer
        return FeatureCommentSerializer
    
    def get_queryset(self):
        feature_id = self.kwargs.get('feature_id')
        return FeatureComment.objects.filter(
            feature_id=feature_id
        ).select_related('author')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        feature_id = self.kwargs.get('feature_id')
        try:
            context['feature'] = Feature.objects.get(pk=feature_id)
        except Feature.DoesNotExist:
            pass
        return context
    
    def create(self, request, *args, **kwargs):
        feature_id = self.kwargs.get('feature_id')
        try:
            Feature.objects.get(pk=feature_id)
        except Feature.DoesNotExist:
            return Response(
                {'error': 'Feature not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return super().create(request, *args, **kwargs)


class FeatureCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a comment. Users can only modify their own comments."""
    
    serializer_class = FeatureCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FeatureComment.objects.select_related('author')
    
    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        # Only the author can update their comment
        if comment.author_id != request.user.id:
            return Response(
                {'error': 'You can only edit your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        # Only the author or a SYSADMIN can delete
        if comment.author_id != request.user.id and request.user.role != 'SYSADMIN':
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# ==================== ADMIN VIEWS (SYSADMIN only) ====================

class FeatureCreateView(generics.CreateAPIView):
    """Create a new feature. SYSADMIN only."""
    
    serializer_class = FeatureWriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]


class FeatureManageView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a feature. SYSADMIN only."""
    
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]
    queryset = Feature.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FeatureWriteSerializer
        return FeatureDetailSerializer


class FeatureStatsView(APIView):
    """Get feature statistics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        total = Feature.objects.count()
        by_status = {
            'planned': Feature.objects.filter(status='planned').count(),
            'in_progress': Feature.objects.filter(status='in_progress').count(),
            'completed': Feature.objects.filter(status='completed').count(),
            'cancelled': Feature.objects.filter(status='cancelled').count(),
        }
        total_comments = FeatureComment.objects.count()
        
        return Response({
            'total_features': total,
            'by_status': by_status,
            'total_comments': total_comments,
        })
