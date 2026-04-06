"""
WebSocket routing configuration for Django Channels.

Defines URL patterns for WebSocket connections.
"""
from django.urls import re_path
from commands.consumers import ScreenConsumer
from commands.dashboard_consumer import AdminDashboardConsumer

websocket_urlpatterns = [
    # WebSocket endpoint for screens
    # Connection URL: ws://server/ws/screen/?auth_token=xxx&secret_key=yyy
    re_path(r'ws/screen/$', ScreenConsumer.as_asgi()),
    
    # WebSocket endpoint for admin dashboard
    # Connection URL: ws://server/ws/dashboard/?token=<JWT_ACCESS_TOKEN>
    re_path(r'ws/dashboard/$', AdminDashboardConsumer.as_asgi()),
]

