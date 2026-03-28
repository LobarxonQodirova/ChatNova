"""
Models for conversations, messages, attachments, and read receipts.
Supports direct messages, group chats, and channels.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from utils.mixins import SoftDeleteMixin, TimeStampedMixin


class Conversation(TimeStampedMixin):
    """
    Represents a conversation container. Can be a direct message,
    group chat, or channel.
    """

    TYPE_CHOICES = [
        ("direct", "Direct Message"),
        ("group", "Group Chat"),
        ("channel", "Channel"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="direct")
    description = models.TextField(max_length=1000, blank=True)
    avatar = models.ImageField(upload_to="conversations/%Y/%m/", blank=True, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ConversationMember",
        related_name="conversations",
    )
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    pinned_message = models.ForeignKey(
        "Message", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    last_message = models.ForeignKey(
        "Message", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    last_activity = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "conversations_conversation"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["type", "last_activity"]),
        ]

    def __str__(self):
        if self.name:
            return self.name
        if self.type == "direct":
            usernames = list(
                self.members.values_list("username", flat=True)[:2]
            )
            return " & ".join(usernames)
        return f"Conversation {self.id}"

    @property
    def member_count(self):
        return self.conversation_members.filter(is_active=True).count()

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    def add_member(self, user, role="member"):
        member, created = ConversationMember.objects.get_or_create(
            conversation=self, user=user, defaults={"role": role}
        )
        if not created and not member.is_active:
            member.is_active = True
            member.save(update_fields=["is_active"])
        return member

    def remove_member(self, user):
        ConversationMember.objects.filter(
            conversation=self, user=user
        ).update(is_active=False, left_at=timezone.now())


class ConversationMember(TimeStampedMixin):
    """Tracks membership and role within a conversation."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="conversation_members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memberships",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)
    is_muted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    nickname = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversations_member"
        unique_together = ["conversation", "user"]
        ordering = ["-is_pinned", "-last_read_at"]

    def __str__(self):
        return f"{self.user.username} in {self.conversation}"

    @property
    def unread_count(self):
        if not self.last_read_at:
            return self.conversation.messages.count()
        return self.conversation.messages.filter(
            created_at__gt=self.last_read_at
        ).exclude(sender=self.user).count()

    def mark_as_read(self):
        self.last_read_at = timezone.now()
        self.save(update_fields=["last_read_at"])


class Message(TimeStampedMixin, SoftDeleteMixin):
    """Individual message within a conversation."""

    TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("audio", "Audio"),
        ("video", "Video"),
        ("system", "System Message"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
    )
    content = models.TextField(max_length=10000)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent_message = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="thread_replies"
    )
    forwarded_from = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="forwards"
    )

    class Meta:
        db_table = "conversations_message"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["parent_message"]),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else "System"
        return f"{sender_name}: {self.content[:50]}"

    @property
    def reply_count(self):
        return self.thread_replies.filter(is_deleted=False).count()

    @property
    def reaction_summary(self):
        reactions = self.reactions.values("emoji").annotate(
            count=models.Count("id")
        ).order_by("-count")
        return {r["emoji"]: r["count"] for r in reactions}

    def edit_message(self, new_content):
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=["content", "is_edited", "edited_at"])


class MessageAttachment(TimeStampedMixin):
    """File attachment associated with a message."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    thumbnail = models.ImageField(
        upload_to="thumbnails/%Y/%m/%d/", blank=True, null=True
    )
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds for audio/video")

    class Meta:
        db_table = "conversations_attachment"
        ordering = ["created_at"]

    def __str__(self):
        return self.filename

    @property
    def file_url(self):
        return self.file.url if self.file else None

    @property
    def is_image(self):
        return self.file_type.startswith("image/")

    @property
    def human_readable_size(self):
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class MessageReaction(TimeStampedMixin):
    """Emoji reaction on a message."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    emoji = models.CharField(max_length=50)

    class Meta:
        db_table = "conversations_reaction"
        unique_together = ["message", "user", "emoji"]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji}"


class ReadReceipt(models.Model):
    """Tracks when a user reads a specific message."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="read_receipts"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="read_receipts",
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversations_read_receipt"
        unique_together = ["message", "user"]
        ordering = ["-read_at"]

    def __str__(self):
        return f"{self.user.username} read at {self.read_at}"
