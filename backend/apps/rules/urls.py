from django.urls import re_path

from .views import (AllRulesView, JobActionDetailView, JobActionListView,
                    JobActionSearchView, RuleCategoryDetailView,
                    RuleCategoryListView, RuleListView, RuleSearchView)

urlpatterns = [
    re_path(r'^/?$', AllRulesView.as_view(), name='all_rules'),
    re_path(r'^categories/?$', RuleCategoryListView.as_view(), name='rule_categories'),
    re_path(r'^categories/(?P<pk>\d+)/?$', RuleCategoryDetailView.as_view(), name='rule_category_detail'),
    re_path(r'^list/?$', RuleListView.as_view(), name='rule_list'),
    re_path(r'^search/?$', RuleSearchView.as_view(), name='rule_search'),
    re_path(r'^jobs/?$', JobActionListView.as_view(), name='job_actions'),
    re_path(r'^jobs/(?P<pk>\d+)/?$', JobActionDetailView.as_view(), name='job_action_detail'),
    re_path(r'^jobs/search/?$', JobActionSearchView.as_view(), name='job_search'),
]
