"""
URL configuration for Elitelupus Staff Toolbox SAAS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/staff/', include('apps.staff.urls')),
    path('api/counters/', include('apps.counters.urls')),
    path('api/servers/', include('apps.servers.urls')),
    path('api/templates/', include('apps.templates_manager.urls')),
    path('api/rules/', include('apps.rules.urls')),
    
    # Social Auth
    path('auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
