"""
Models for group chats: Group, GroupMember, GroupMessage, GroupSettings.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from utils.mixins import SoftDeleteMixin, TimeStampedMixin


class Group(TimeStampedMixin):
    """
    A group chat with members, admin controls, and customizable settings.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True)
    avatar = models.ImageField(upload_to="groups/%Y/%m/", blank=True, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_groups",
    )
    invite_link = models.CharField(max_length=64, unique=True, blank=True, null=True)
    is_public = models.BooleanField(
        default=False, help_text="Public groups can be found via search."
    )
    max_members = models.PositiveIntegerField(default=256)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "groups_group"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["is_public", "-last_activity"]),
            models.Index(fields=["invite_link"]),
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.filter(is_active=True).count()

    def generate_invite_link(self):
        import secrets

        self.invite_link = secrets.token_urlsafe(32)
        self.save(update_fields=["invite_link"])
        return self.invite_link

    def add_member(self, user, role="member"):
        if self.member_count >= self.max_members:
            raise ValueError("Group has reached maximum capacity.")
        member, created = GroupMember.objects.get_or_create(
            group=self, user=user, defaults={"role": role}
        )
        if not created and not member.is_active:
            member.is_active = True
            member.role = role
            member.save(update_fields=["is_active", "role"])
        return member

    def remove_member(self, user):
        GroupMember.objects.filter(group=self, user=user).update(
            is_active=False, left_at=timezone.now()
        )


class GroupMember(TimeStampedMixin):
    """Tracks group membership with roles and permissions."""

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("member", "Member"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)
    is_muted = models.BooleanField(default=False)
    nickname = models.CharField(max_length=100, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_message = models.ForeignKey(
        "GroupMessage", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "groups_member"
        unique_together = ["group", "user"]
        ordering = ["role", "joined_at"]

    def __str__(self):
        return f"{self.user.username} ({self.role}) in {self.group.name}"

    @property
    def can_manage(self):
        return self.role in ("owner", "admin", "moderator")

    @property
    def can_admin(self):
        return self.role in ("owner", "admin")

    def promote(self, new_role):
        role_hierarchy = {"member": 0, "moderator": 1, "admin": 2, "owner": 3}
        if role_hierarchy.get(new_role, 0) > role_hierarchy.get(self.role, 0):
            self.role = new_role
            self.save(update_fields=["role"])


class GroupMessage(TimeStampedMixin, SoftDeleteMixin):
    """A message sent within a group chat."""

    TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("audio", "Audio"),
        ("video", "Video"),
        ("system", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="group_messages",
    )
    content = models.TextField(max_length=10000)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )
    attachment = models.FileField(upload_to="group_attachments/%Y/%m/%d/", blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True)
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="group_mentions"
    )

    class Meta:
        db_table = "groups_message"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "-created_at"]),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else "System"
        return f"[{self.group.name}] {sender_name}: {self.content[:50]}"

    def edit_message(self, new_content):
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=["content", "is_edited", "edited_at"])


class GroupSettings(TimeStampedMixin):
    """Per-group configuration controlled by admins."""

    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="settings", primary_key=True
    )
    only_admins_can_post = models.BooleanField(
        default=False, help_text="Only admins and moderators can send messages."
    )
    only_admins_can_edit_info = models.BooleanField(
        default=True, help_text="Only admins can change group name/description."
    )
    member_can_invite = models.BooleanField(
        default=True, help_text="Non-admin members can share the invite link."
    )
    approve_new_members = models.BooleanField(
        default=False, help_text="New join requests require admin approval."
    )
    message_retention_days = models.PositiveIntegerField(
        default=0, help_text="Auto-delete messages after N days. 0 = keep forever."
    )
    slow_mode_seconds = models.PositiveIntegerField(
        default=0, help_text="Minimum seconds between messages per user. 0 = disabled."
    )

    class Meta:
        db_table = "groups_settings"

    def __str__(self):
        return f"Settings for {self.group.name}"
