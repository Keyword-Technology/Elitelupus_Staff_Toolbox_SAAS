from django.urls import re_path

from .views import (
    FeatureCommentDetailView,
    FeatureCommentListCreateView,
    FeatureCreateView,
    FeatureDetailView,
    FeatureListView,
    FeatureManageView,
    FeatureStatsView,
)

urlpatterns = [
    # Public endpoints (all authenticated users)
    re_path(r'^/?$', FeatureListView.as_view(), name='feature_list'),
    re_path(r'^stats/?$', FeatureStatsView.as_view(), name='feature_stats'),
    re_path(r'^(?P<pk>\d+)/?$', FeatureDetailView.as_view(), name='feature_detail'),
    re_path(r'^(?P<feature_id>\d+)/comments/?$', FeatureCommentListCreateView.as_view(), name='feature_comments'),
    re_path(r'^comments/(?P<pk>\d+)/?$', FeatureCommentDetailView.as_view(), name='comment_detail'),
    
    # Admin endpoints (SYSADMIN only)
    re_path(r'^create/?$', FeatureCreateView.as_view(), name='feature_create'),
    re_path(r'^(?P<pk>\d+)/manage/?$', FeatureManageView.as_view(), name='feature_manage'),
]
