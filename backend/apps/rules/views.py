from apps.accounts.permissions import IsManager, IsModerator
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobAction, Rule, RuleCategory
from .serializers import (JobActionSerializer, JobActionWriteSerializer,
                          RuleCategoryListSerializer, RuleCategorySerializer,
                          RuleCategoryWriteSerializer, RuleSerializer,
                          RuleWriteSerializer)


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


# ==================== MANAGEMENT VIEWS ====================
# These views require Manager role or higher (sysadmin/manager)

class RuleCategoryManageView(generics.ListCreateAPIView):
    """List all categories (including inactive) and create new categories."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RuleCategoryWriteSerializer
        return RuleCategorySerializer
    
    def get_queryset(self):
        return RuleCategory.objects.all().prefetch_related('rules')


class RuleCategoryDetailManageView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific category."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    queryset = RuleCategory.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RuleCategoryWriteSerializer
        return RuleCategorySerializer


class RuleManageView(generics.ListCreateAPIView):
    """List all rules (including inactive) and create new rules."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RuleWriteSerializer
        return RuleSerializer
    
    def get_queryset(self):
        queryset = Rule.objects.all().select_related('category')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset


class RuleDetailManageView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific rule."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    queryset = Rule.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RuleWriteSerializer
        return RuleSerializer


class JobActionManageView(generics.ListCreateAPIView):
    """List all job actions (including inactive) and create new ones."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobActionWriteSerializer
        return JobActionSerializer
    
    def get_queryset(self):
        return JobAction.objects.all()


class JobActionDetailManageView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific job action."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    queryset = JobAction.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobActionWriteSerializer
        return JobActionSerializer


class BulkRuleImportView(APIView):
    """Bulk import rules from structured data."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def post(self, request):
        """
        Import rules in bulk. Expected format:
        {
            "categories": [
                {
                    "name": "Category Name",
                    "description": "Optional description",
                    "rules": [
                        {"code": "1.1", "title": "Rule Title", "content": "Rule content"}
                    ]
                }
            ]
        }
        """
        data = request.data
        categories_data = data.get('categories', [])
        
        created_categories = 0
        created_rules = 0
        errors = []
        
        for cat_data in categories_data:
            try:
                category, cat_created = RuleCategory.objects.update_or_create(
                    name=cat_data.get('name'),
                    defaults={
                        'description': cat_data.get('description', ''),
                        'order': cat_data.get('order', 0),
                        'is_active': cat_data.get('is_active', True),
                    }
                )
                if cat_created:
                    created_categories += 1
                
                for rule_data in cat_data.get('rules', []):
                    try:
                        rule, rule_created = Rule.objects.update_or_create(
                            category=category,
                            code=rule_data.get('code'),
                            defaults={
                                'title': rule_data.get('title', ''),
                                'content': rule_data.get('content', ''),
                                'order': rule_data.get('order', 0),
                                'is_active': rule_data.get('is_active', True),
                            }
                        )
                        if rule_created:
                            created_rules += 1
                    except Exception as e:
                        errors.append(f"Error importing rule {rule_data.get('code')}: {str(e)}")
            except Exception as e:
                errors.append(f"Error importing category {cat_data.get('name')}: {str(e)}")
        
        return Response({
            'created_categories': created_categories,
            'created_rules': created_rules,
            'errors': errors
        }, status=status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS)
