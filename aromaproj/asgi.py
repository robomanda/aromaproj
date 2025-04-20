
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from qrmenu.consumers import OrderConsumer  # You'll need to create this consumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aromaproj.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # Define WebSocket URL path for orders
            path("ws/orders/", OrderConsumer.as_asgi()),
        ])
    ),
})
