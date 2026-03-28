"""
Serializers for conversations, messages, attachments, and related resources.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import (
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageReaction,
    ReadReceipt,
)

User = get_user_model()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message file attachments."""

    file_url = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    human_readable_size = serializers.ReadOnlyField()

    class Meta:
        model = MessageAttachment
        fields = [
            "id", "file", "filename", "file_type", "file_size",
            "thumbnail", "width", "height", "duration",
            "file_url", "is_image", "human_readable_size", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for emoji reactions."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ["id", "emoji", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class ReadReceiptSerializer(serializers.ModelSerializer):
    """Serializer for read receipts."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ReadReceipt
        fields = ["id", "user", "read_at"]
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Full message serializer with nested attachments and reactions."""

    sender = UserMinimalSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reaction_summary = serializers.ReadOnlyField()
    reply_count = serializers.ReadOnlyField()
    is_own_message = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "sender", "content", "type",
            "is_edited", "edited_at", "parent_message", "forwarded_from",
            "attachments", "reaction_summary", "reply_count",
            "is_own_message", "is_deleted", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "sender", "is_edited", "edited_at", "is_deleted",
            "created_at", "updated_at",
        ]

    def get_is_own_message(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message."""

    attachments = serializers.ListField(
        child=serializers.FileField(), required=False, write_only=True
    )

    class Meta:
        model = Message
        fields = ["content", "type", "parent_message", "attachments"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value

    def create(self, validated_data):
        attachment_files = validated_data.pop("attachments", [])
        message = Message.objects.create(**validated_data)

        for file in attachment_files:
            MessageAttachment.objects.create(
                message=message,
                file=file,
                filename=file.name,
                file_type=file.content_type or "application/octet-stream",
                file_size=file.size,
            )

        return message


class ConversationMemberSerializer(serializers.ModelSerializer):
    """Serializer for conversation membership."""

    user = UserMinimalSerializer(read_only=True)
    unread_count = serializers.ReadOnlyField()

    class Meta:
        model = ConversationMember
        fields = [
            "id", "user", "role", "is_active", "is_muted",
            "is_pinned", "nickname", "joined_at", "last_read_at",
            "unread_count",
        ]
        read_only_fields = ["id", "user", "joined_at"]


class ConversationSerializer(serializers.ModelSerializer):
    """Full conversation serializer with latest message and members."""

    creator = UserMinimalSerializer(read_only=True)
    last_message = MessageSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    members_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "name", "type", "description", "avatar",
            "creator", "member_count", "members_preview",
            "last_message", "last_activity", "is_archived",
            "unread_count", "created_at",
        ]
        read_only_fields = ["id", "creator", "last_activity", "created_at"]

    def get_members_preview(self, obj):
        members = obj.conversation_members.filter(
            is_active=True
        ).select_related("user")[:5]
        return ConversationMemberSerializer(members, many=True).data

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            membership = obj.conversation_members.filter(
                user=request.user, is_active=True
            ).first()
            return membership.unread_count if membership else 0
        return 0


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer for creating a new conversation."""

    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=Conversation.TYPE_CHOICES, default="direct")
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1
    )

    def validate_member_ids(self, value):
        users = User.objects.filter(id__in=value, is_active=True)
        if users.count() != len(value):
            raise serializers.ValidationError("One or more users not found.")
        return value

    def validate(self, data):
        if data.get("type") == "direct" and len(data["member_ids"]) != 1:
            raise serializers.ValidationError(
                "Direct messages must have exactly one other member."
            )
        return data

    def create(self, validated_data):
        member_ids = validated_data.pop("member_ids")
        creator = self.context["request"].user

        # For direct messages, check if conversation already exists
        if validated_data.get("type") == "direct":
            other_user_id = member_ids[0]
            existing = Conversation.objects.filter(
                type="direct",
                conversation_members__user=creator,
            ).filter(
                conversation_members__user_id=other_user_id,
            ).first()
            if existing:
                return existing

        conversation = Conversation.objects.create(creator=creator, **validated_data)
        conversation.add_member(creator, role="owner")
        for user_id in member_ids:
            user = User.objects.get(id=user_id)
            conversation.add_member(user)

        return conversation
