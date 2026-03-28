"""
Models for user notifications.
"""
import uuid

from django.conf import settings
from django.db import models

from utils.mixins import TimeStampedMixin


class Notification(TimeStampedMixin):
    """
    A notification sent to a user about an event in the application.
    Supports different types: message, mention, reaction, contact request, etc.
    """

    TYPE_CHOICES = [
        ("message", "New Message"),
        ("mention", "Mentioned"),
        ("reaction", "Reaction"),
        ("contact_request", "Contact Request"),
        ("contact_accepted", "Contact Accepted"),
        ("group_invite", "Group Invite"),
        ("group_mention", "Group Mention"),
        ("system", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=1000, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Generic reference to related object
    target_type = models.CharField(
        max_length=50, blank=True,
        help_text="Model type of the related object (e.g., 'conversation', 'group').",
    )
    target_id = models.UUIDField(
        null=True, blank=True,
        help_text="ID of the related object.",
    )

    # Optional action URL for the frontend
    action_url = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["recipient", "type"]),
        ]

    def __str__(self):
        return f"[{self.type}] {self.title} -> {self.recipient.username}"

    def mark_as_read(self):
        from django.utils import timezone

        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @classmethod
    def unread_count(cls, user):
        return cls.objects.filter(recipient=user, is_read=False).count()
