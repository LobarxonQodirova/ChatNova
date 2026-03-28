"""
URL patterns for conversations and messages.
"""
from django.urls import path

from . import views

app_name = "conversations"

urlpatterns = [
    # Conversations
    path("", views.ConversationListCreateView.as_view(), name="list-create"),
    path("<uuid:id>/", views.ConversationDetailView.as_view(), name="detail"),
    path("<uuid:conversation_id>/members/", views.ConversationMembersView.as_view(), name="members"),
    path("<uuid:conversation_id>/read/", views.MarkReadView.as_view(), name="mark-read"),

    # Messages
    path("<uuid:conversation_id>/messages/", views.MessageListCreateView.as_view(), name="messages"),
    path("messages/<uuid:id>/", views.MessageDetailView.as_view(), name="message-detail"),
    path("messages/<uuid:message_id>/reactions/", views.MessageReactionView.as_view(), name="reactions"),
    path("messages/<uuid:message_id>/pin/", views.PinMessageView.as_view(), name="pin"),
    path("messages/<uuid:message_id>/thread/", views.ThreadRepliesView.as_view(), name="thread"),
]
