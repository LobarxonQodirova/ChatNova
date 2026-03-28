"""
Serializers for group chats, members, messages, and settings.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import Group, GroupMember, GroupMessage, GroupSettings

User = get_user_model()


class GroupSettingsSerializer(serializers.ModelSerializer):
    """Serializer for group settings."""

    class Meta:
        model = GroupSettings
        fields = [
            "only_admins_can_post", "only_admins_can_edit_info",
            "member_can_invite", "approve_new_members",
            "message_retention_days", "slow_mode_seconds",
        ]


class GroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for group membership information."""

    user = UserMinimalSerializer(read_only=True)
    can_manage = serializers.ReadOnlyField()
    can_admin = serializers.ReadOnlyField()

    class Meta:
        model = GroupMember
        fields = [
            "id", "user", "role", "is_active", "is_muted",
            "nickname", "joined_at", "can_manage", "can_admin",
        ]
        read_only_fields = ["id", "user", "joined_at"]


class GroupMessageSerializer(serializers.ModelSerializer):
    """Full serializer for a group message."""

    sender = UserMinimalSerializer(read_only=True)
    reply_to_preview = serializers.SerializerMethodField()
    is_own_message = serializers.SerializerMethodField()

    class Meta:
        model = GroupMessage
        fields = [
            "id", "group", "sender", "content", "type",
            "is_edited", "edited_at", "reply_to", "reply_to_preview",
            "attachment", "attachment_name", "attachment_size",
            "is_own_message", "is_deleted", "created_at",
        ]
        read_only_fields = [
            "id", "sender", "is_edited", "edited_at",
            "is_deleted", "created_at",
        ]

    def get_reply_to_preview(self, obj):
        if obj.reply_to and not obj.reply_to.is_deleted:
            return {
                "id": str(obj.reply_to.id),
                "sender": obj.reply_to.sender.username if obj.reply_to.sender else "System",
                "content": obj.reply_to.content[:100],
            }
        return None

    def get_is_own_message(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        return False


class GroupMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for sending a message in a group."""

    class Meta:
        model = GroupMessage
        fields = ["content", "type", "reply_to", "attachment"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


class GroupSerializer(serializers.ModelSerializer):
    """Full group serializer with member preview and settings."""

    creator = UserMinimalSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    settings = GroupSettingsSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id", "name", "description", "avatar", "creator",
            "is_public", "max_members", "member_count",
            "invite_link", "is_active", "last_activity",
            "settings", "is_member", "user_role",
            "latest_message", "created_at",
        ]
        read_only_fields = [
            "id", "creator", "invite_link", "last_activity", "created_at",
        ]

    def get_is_member(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.members.filter(
                user=request.user, is_active=True
            ).exists()
        return False

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            member = obj.members.filter(
                user=request.user, is_active=True
            ).first()
            return member.role if member else None
        return None

    def get_latest_message(self, obj):
        msg = obj.messages.filter(is_deleted=False).first()
        if msg:
            return {
                "id": str(msg.id),
                "sender": msg.sender.username if msg.sender else "System",
                "content": msg.content[:100],
                "created_at": msg.created_at.isoformat(),
            }
        return None


class GroupCreateSerializer(serializers.Serializer):
    """Serializer for creating a new group."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    is_public = serializers.BooleanField(default=False)
    max_members = serializers.IntegerField(default=256, min_value=2, max_value=5000)
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False
    )

    def create(self, validated_data):
        member_ids = validated_data.pop("member_ids", [])
        creator = self.context["request"].user

        group = Group.objects.create(creator=creator, **validated_data)
        GroupSettings.objects.create(group=group)
        group.add_member(creator, role="owner")

        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id, is_active=True)
                group.add_member(user)
            except User.DoesNotExist:
                continue

        group.generate_invite_link()
        return group
