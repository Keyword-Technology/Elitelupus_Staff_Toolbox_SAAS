from django.urls import re_path

from .views import (RefundQuestionTemplateView, RefundTemplateDetailView,
                    RefundTemplateListCreateView, ResponseTemplateDetailView,
                    ResponseTemplateListCreateView,
                    SteamProfileHistoryListView, SteamProfileLookupView,
                    SteamProfileSearchDetailView, SteamProfileSearchListView,
                    TemplateCategoryListView)

urlpatterns = [
    re_path(r'^refunds/?$', RefundTemplateListCreateView.as_view(), name='refund_list'),
    re_path(r'^refunds/(?P<pk>\d+)/?$', RefundTemplateDetailView.as_view(), name='refund_detail'),
    re_path(r'^categories/?$', TemplateCategoryListView.as_view(), name='template_categories'),
    re_path(r'^responses/?$', ResponseTemplateListCreateView.as_view(), name='response_templates'),
    re_path(r'^responses/(?P<pk>\d+)/?$', ResponseTemplateDetailView.as_view(), name='response_detail'),
    re_path(r'^steam-lookup/?$', SteamProfileLookupView.as_view(), name='steam_lookup'),
    re_path(r'^steam-searches/?$', SteamProfileSearchListView.as_view(), name='steam_searches'),
    re_path(r'^steam-searches/(?P<steam_id_64>[^/]+)/?$', SteamProfileSearchDetailView.as_view(), name='steam_search_detail'),
    re_path(r'^steam-history/?$', SteamProfileHistoryListView.as_view(), name='steam_history'),
    re_path(r'^refund-question/?$', RefundQuestionTemplateView.as_view(), name='refund_question'),
]
