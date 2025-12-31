"""
URL configuration for Elitelupus Staff Toolbox SAAS project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/staff/', include('apps.staff.urls')),
    path('api/counters/', include('apps.counters.urls')),
    path('api/servers/', include('apps.servers.urls')),
    path('api/templates/', include('apps.templates_manager.urls')),
    path('api/rules/', include('apps.rules.urls')),
    path('api/system/', include('apps.system_settings.urls')),
    
    # OAuth (Steam, Discord, etc.)
    path('api/oauth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
