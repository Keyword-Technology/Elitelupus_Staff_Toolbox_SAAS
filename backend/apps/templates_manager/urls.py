from django.urls import path
from .views import (
    RefundTemplateListCreateView,
    RefundTemplateDetailView,
    TemplateCategoryListView,
    ResponseTemplateListCreateView,
    ResponseTemplateDetailView,
    SteamProfileLookupView,
    RefundQuestionTemplateView,
)

urlpatterns = [
    path('refunds/', RefundTemplateListCreateView.as_view(), name='refund_list'),
    path('refunds/<int:pk>/', RefundTemplateDetailView.as_view(), name='refund_detail'),
    path('categories/', TemplateCategoryListView.as_view(), name='template_categories'),
    path('responses/', ResponseTemplateListCreateView.as_view(), name='response_templates'),
    path('responses/<int:pk>/', ResponseTemplateDetailView.as_view(), name='response_detail'),
    path('steam-lookup/', SteamProfileLookupView.as_view(), name='steam_lookup'),
    path('refund-question/', RefundQuestionTemplateView.as_view(), name='refund_question'),
]
