"""
WebSocket URL routing for the chat app.
These patterns are included in the main config/routing.py.
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<conversation_id>[0-9a-f-]+)/$",
        consumers.ChatConsumer.as_asgi(),
    ),
]
