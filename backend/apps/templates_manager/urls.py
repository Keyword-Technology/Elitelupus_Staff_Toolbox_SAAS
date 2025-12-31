from django.urls import path

from .views import (RefundQuestionTemplateView, RefundTemplateDetailView,
                    RefundTemplateListCreateView, ResponseTemplateDetailView,
                    ResponseTemplateListCreateView,
                    SteamProfileHistoryListView, SteamProfileLookupView,
                    SteamProfileSearchDetailView, SteamProfileSearchListView,
                    TemplateCategoryListView)

urlpatterns = [
    path('refunds/', RefundTemplateListCreateView.as_view(), name='refund_list'),
    path('refunds/<int:pk>/', RefundTemplateDetailView.as_view(), name='refund_detail'),
    path('categories/', TemplateCategoryListView.as_view(), name='template_categories'),
    path('responses/', ResponseTemplateListCreateView.as_view(), name='response_templates'),
    path('responses/<int:pk>/', ResponseTemplateDetailView.as_view(), name='response_detail'),
    path('steam-lookup/', SteamProfileLookupView.as_view(), name='steam_lookup'),
    path('steam-searches/', SteamProfileSearchListView.as_view(), name='steam_searches'),
    path('steam-searches/<str:steam_id_64>/', SteamProfileSearchDetailView.as_view(), name='steam_search_detail'),
    path('steam-history/', SteamProfileHistoryListView.as_view(), name='steam_history'),
    path('refund-question/', RefundQuestionTemplateView.as_view(), name='refund_question'),
]
