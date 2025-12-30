from django.urls import path
from .views import (
    RuleCategoryListView,
    RuleCategoryDetailView,
    RuleListView,
    RuleSearchView,
    JobActionListView,
    JobActionDetailView,
    JobActionSearchView,
    AllRulesView,
)

urlpatterns = [
    path('', AllRulesView.as_view(), name='all_rules'),
    path('categories/', RuleCategoryListView.as_view(), name='rule_categories'),
    path('categories/<int:pk>/', RuleCategoryDetailView.as_view(), name='rule_category_detail'),
    path('list/', RuleListView.as_view(), name='rule_list'),
    path('search/', RuleSearchView.as_view(), name='rule_search'),
    path('jobs/', JobActionListView.as_view(), name='job_actions'),
    path('jobs/<int:pk>/', JobActionDetailView.as_view(), name='job_action_detail'),
    path('jobs/search/', JobActionSearchView.as_view(), name='job_search'),
]
