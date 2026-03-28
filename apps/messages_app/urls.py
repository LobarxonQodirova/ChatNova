"""
URL patterns for messages - delegates to conversations app.
Kept for backward compatibility with config/urls.py.
"""
from django.urls import path

from apps.conversations.views import (
    MessageDetailView,
    MessageReactionView,
    PinMessageView,
    ThreadRepliesView,
)

app_name = "messages_app"

urlpatterns = [
    path("<uuid:id>/", MessageDetailView.as_view(), name="detail"),
    path("<uuid:message_id>/reactions/", MessageReactionView.as_view(), name="reactions"),
    path("<uuid:message_id>/pin/", PinMessageView.as_view(), name="pin"),
    path("<uuid:message_id>/thread/", ThreadRepliesView.as_view(), name="thread"),
]
