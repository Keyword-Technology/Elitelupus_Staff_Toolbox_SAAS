from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import RuleCategory, Rule, JobAction
from .serializers import (
    RuleCategorySerializer,
    RuleCategoryListSerializer,
    RuleSerializer,
    JobActionSerializer,
)
from apps.accounts.permissions import IsModerator


class RuleCategoryListView(generics.ListAPIView):
    """List all rule categories."""
    serializer_class = RuleCategoryListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = RuleCategory.objects.filter(is_active=True)


class RuleCategoryDetailView(generics.RetrieveAPIView):
    """Get a rule category with all its rules."""
    serializer_class = RuleCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = RuleCategory.objects.filter(is_active=True)


class RuleListView(generics.ListAPIView):
    """List all rules, optionally filtered by category."""
    serializer_class = RuleSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Rule.objects.filter(is_active=True)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset


class RuleSearchView(APIView):
    """Search rules by keyword."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])
        
        rules = Rule.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(code__icontains=query)
        )[:20]
        
        return Response(RuleSerializer(rules, many=True).data)


class JobActionListView(generics.ListAPIView):
    """List all job actions."""
    serializer_class = JobActionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = JobAction.objects.filter(is_active=True)


class JobActionDetailView(generics.RetrieveAPIView):
    """Get a specific job's actions."""
    serializer_class = JobActionSerializer
    permission_classes = [permissions.AllowAny]
    queryset = JobAction.objects.filter(is_active=True)


class JobActionSearchView(APIView):
    """Search job actions by job name."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])
        
        jobs = JobAction.objects.filter(
            is_active=True,
            job_name__icontains=query
        )[:10]
        
        return Response(JobActionSerializer(jobs, many=True).data)


class AllRulesView(APIView):
    """Get all rules organized by category."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = RuleCategory.objects.filter(
            is_active=True
        ).prefetch_related('rules')
        
        return Response(RuleCategorySerializer(categories, many=True).data)
