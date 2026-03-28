"""
Custom user model and profile for ChatNova.
Extends AbstractUser with messaging-specific fields.
"""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.mixins import TimeStampedMixin


class User(AbstractUser):
    """Custom user model with additional profile and presence fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Presence
    STATUS_CHOICES = [
        ("online", "Online"),
        ("away", "Away"),
        ("dnd", "Do Not Disturb"),
        ("offline", "Offline"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="offline")
    custom_status = models.CharField(max_length=200, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    # Preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    theme = models.CharField(
        max_length=10,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        default="system",
    )

    # Meta
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["username"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["last_seen"]),
        ]

    def __str__(self):
        return self.display_name or self.username

    @property
    def full_display_name(self):
        return self.display_name or self.get_full_name() or self.username

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    def set_online(self):
        from django.utils import timezone

        self.status = "online"
        self.last_seen = timezone.now()
        self.save(update_fields=["status", "last_seen"])

    def set_offline(self):
        from django.utils import timezone

        self.status = "offline"
        self.last_seen = timezone.now()
        self.save(update_fields=["status", "last_seen"])


class UserProfile(TimeStampedMixin):
    """Extended profile settings for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    message_preview = models.BooleanField(
        default=True, help_text="Show message content in notifications"
    )
    read_receipts = models.BooleanField(
        default=True, help_text="Let others know when you've read their messages"
    )
    typing_indicators = models.BooleanField(
        default=True, help_text="Show when you are typing"
    )

    class Meta:
        db_table = "accounts_user_profile"

    def __str__(self):
        return f"Profile for {self.user.username}"
