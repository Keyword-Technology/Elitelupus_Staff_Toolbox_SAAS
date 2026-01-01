"""
ASGI config for Elitelupus Staff Toolbox SAAS project.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from apps.accounts.middleware import JWTAuthMiddlewareStack
from apps.counters.routing import websocket_urlpatterns as counter_ws
from apps.servers.routing import websocket_urlpatterns as server_ws
from apps.staff.routing import websocket_urlpatterns as staff_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                counter_ws + server_ws + staff_ws
            )
        )
    ),
})
