from django.urls import re_path

from .views import (AllRulesView, BulkRuleImportView,
                    JobActionDetailManageView, JobActionDetailView,
                    JobActionListView, JobActionManageView,
                    JobActionSearchView, RuleCategoryDetailManageView,
                    RuleCategoryDetailView, RuleCategoryListView,
                    RuleCategoryManageView, RuleDetailManageView, RuleListView,
                    RuleManageView, RuleSearchView)

urlpatterns = [
    # Public read-only endpoints
    re_path(r'^/?$', AllRulesView.as_view(), name='all_rules'),
    re_path(r'^categories/?$', RuleCategoryListView.as_view(), name='rule_categories'),
    re_path(r'^categories/(?P<pk>\d+)/?$', RuleCategoryDetailView.as_view(), name='rule_category_detail'),
    re_path(r'^list/?$', RuleListView.as_view(), name='rule_list'),
    re_path(r'^search/?$', RuleSearchView.as_view(), name='rule_search'),
    re_path(r'^jobs/?$', JobActionListView.as_view(), name='job_actions'),
    re_path(r'^jobs/(?P<pk>\d+)/?$', JobActionDetailView.as_view(), name='job_action_detail'),
    re_path(r'^jobs/search/?$', JobActionSearchView.as_view(), name='job_search'),
    
    # Management endpoints (Manager+ only)
    re_path(r'^manage/categories/?$', RuleCategoryManageView.as_view(), name='manage_categories'),
    re_path(r'^manage/categories/(?P<pk>\d+)/?$', RuleCategoryDetailManageView.as_view(), name='manage_category_detail'),
    re_path(r'^manage/rules/?$', RuleManageView.as_view(), name='manage_rules'),
    re_path(r'^manage/rules/(?P<pk>\d+)/?$', RuleDetailManageView.as_view(), name='manage_rule_detail'),
    re_path(r'^manage/jobs/?$', JobActionManageView.as_view(), name='manage_jobs'),
    re_path(r'^manage/jobs/(?P<pk>\d+)/?$', JobActionDetailManageView.as_view(), name='manage_job_detail'),
    re_path(r'^manage/import/?$', BulkRuleImportView.as_view(), name='bulk_import'),
]
