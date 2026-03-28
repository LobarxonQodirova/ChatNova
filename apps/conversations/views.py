"""
Views for conversation and message CRUD operations.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.pagination import MessageCursorPagination

from .models import (
    Conversation,
    ConversationMember,
    Message,
    MessageReaction,
    ReadReceipt,
)
from .serializers import (
    ConversationCreateSerializer,
    ConversationMemberSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ReadReceiptSerializer,
)

User = get_user_model()


class ConversationListCreateView(generics.ListCreateAPIView):
    """List all conversations for the current user, or create a new one."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.filter(
            conversation_members__user=user,
            conversation_members__is_active=True,
        ).select_related("creator", "last_message__sender").prefetch_related(
            "conversation_members__user"
        ).distinct()

        conv_type = self.request.query_params.get("type")
        if conv_type:
            queryset = queryset.filter(type=conv_type)

        archived = self.request.query_params.get("archived")
        if archived is not None:
            queryset = queryset.filter(is_archived=archived.lower() == "true")
        else:
            queryset = queryset.filter(is_archived=False)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(conversation_members__user__username__icontains=search)
            ).distinct()

        return queryset.order_by("-last_activity")

    def create(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or archive a conversation."""

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Conversation.objects.filter(
            conversation_members__user=self.request.user,
            conversation_members__is_active=True,
        )

    def perform_destroy(self, instance):
        """Archive instead of deleting."""
        instance.is_archived = True
        instance.save(update_fields=["is_archived"])


class ConversationMembersView(APIView):
    """Manage members of a conversation."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation, id=conversation_id,
            conversation_members__user=request.user,
            conversation_members__is_active=True,
        )
        members = conversation.conversation_members.filter(
            is_active=True
        ).select_related("user")
        serializer = ConversationMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        membership = get_object_or_404(
            ConversationMember, conversation=conversation,
            user=request.user, is_active=True,
        )

        if membership.role not in ("owner", "admin"):
            return Response(
                {"error": {"code": "forbidden", "message": "Only admins can add members."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": {"code": "validation", "message": "user_id is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id, is_active=True)
        member = conversation.add_member(user)

        # Create system message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{user.username} was added to the conversation.",
            type="system",
        )

        return Response(
            ConversationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        user_id = request.data.get("user_id")

        if str(user_id) == str(request.user.id):
            # User leaving the conversation
            conversation.remove_member(request.user)
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=f"{request.user.username} left the conversation.",
                type="system",
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        membership = get_object_or_404(
            ConversationMember, conversation=conversation,
            user=request.user, is_active=True,
        )
        if membership.role not in ("owner", "admin"):
            return Response(
                {"error": {"code": "forbidden", "message": "Only admins can remove members."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = get_object_or_404(User, id=user_id)
        conversation.remove_member(user)

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f"{user.username} was removed from the conversation.",
            type="system",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageListCreateView(generics.ListCreateAPIView):
    """List messages in a conversation or send a new message."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        get_object_or_404(
            ConversationMember,
            conversation_id=conversation_id,
            user=self.request.user,
            is_active=True,
        )
        return (
            Message.objects.filter(
                conversation_id=conversation_id, is_deleted=False
            )
            .select_related("sender")
            .prefetch_related("attachments", "reactions__user")
        )

    def perform_create(self, serializer):
        conversation_id = self.kwargs["conversation_id"]
        conversation = get_object_or_404(Conversation, id=conversation_id)
        get_object_or_404(
            ConversationMember,
            conversation=conversation,
            user=self.request.user,
            is_active=True,
        )
        message = serializer.save(
            sender=self.request.user, conversation=conversation
        )
        conversation.last_message = message
        conversation.save(update_fields=["last_message", "last_activity"])
        return message


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, edit, or soft-delete a specific message."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Message.objects.filter(
            sender=self.request.user, is_deleted=False
        )

    def perform_update(self, serializer):
        message = self.get_object()
        new_content = self.request.data.get("content", message.content)
        message.edit_message(new_content)

    def perform_destroy(self, instance):
        instance.soft_delete()


class MessageReactionView(APIView):
    """Add or remove emoji reactions on a message."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, is_deleted=False)
        emoji = request.data.get("emoji")
        if not emoji:
            return Response(
                {"error": {"code": "validation", "message": "emoji is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reaction, created = MessageReaction.objects.get_or_create(
            message=message, user=request.user, emoji=emoji,
        )
        if not created:
            reaction.delete()
            return Response(
                {"message": "Reaction removed."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "Reaction added.", "emoji": emoji},
            status=status.HTTP_201_CREATED,
        )


class PinMessageView(APIView):
    """Pin or unpin a message in its conversation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, is_deleted=False)
        conversation = message.conversation

        get_object_or_404(
            ConversationMember,
            conversation=conversation,
            user=request.user,
            is_active=True,
        )

        if conversation.pinned_message_id == message.id:
            conversation.pinned_message = None
            conversation.save(update_fields=["pinned_message"])
            return Response({"message": "Message unpinned."})

        conversation.pinned_message = message
        conversation.save(update_fields=["pinned_message"])
        return Response({"message": "Message pinned."})


class ThreadRepliesView(generics.ListAPIView):
    """List all replies in a message thread."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        message_id = self.kwargs["message_id"]
        parent_message = get_object_or_404(Message, id=message_id)
        get_object_or_404(
            ConversationMember,
            conversation=parent_message.conversation,
            user=self.request.user,
            is_active=True,
        )
        return Message.objects.filter(
            parent_message=parent_message, is_deleted=False
        ).select_related("sender").prefetch_related("attachments", "reactions__user")


class MarkReadView(APIView):
    """Mark messages as read up to a certain point."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        membership = get_object_or_404(
            ConversationMember,
            conversation_id=conversation_id,
            user=request.user,
            is_active=True,
        )
        membership.mark_as_read()

        message_id = request.data.get("message_id")
        if message_id:
            message = get_object_or_404(
                Message, id=message_id, conversation_id=conversation_id
            )
            ReadReceipt.objects.get_or_create(
                message=message, user=request.user,
            )

        return Response({"message": "Marked as read."})
