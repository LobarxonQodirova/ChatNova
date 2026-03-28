"""
Models for contacts, contact groups, and blocked users.
"""
import uuid

from django.conf import settings
from django.db import models

from utils.mixins import TimeStampedMixin


class Contact(TimeStampedMixin):
    """
    Represents a user's contact - a saved reference to another user.
    Contacts are directional (user saves contact_user).
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text="The user who owns this contact.",
    )
    contact_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacted_by",
        help_text="The user being saved as a contact.",
    )
    nickname = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    is_favorite = models.BooleanField(default=False)
    notes = models.TextField(max_length=500, blank=True)

    class Meta:
        db_table = "contacts_contact"
        unique_together = ["user", "contact_user"]
        ordering = ["contact_user__username"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "is_favorite"]),
        ]

    def __str__(self):
        display = self.nickname or self.contact_user.username
        return f"{self.user.username} -> {display}"

    def accept(self):
        self.status = "accepted"
        self.save(update_fields=["status"])
        # Create reverse contact
        Contact.objects.get_or_create(
            user=self.contact_user,
            contact_user=self.user,
            defaults={"status": "accepted"},
        )

    def decline(self):
        self.status = "declined"
        self.save(update_fields=["status"])


class ContactGroup(TimeStampedMixin):
    """
    Named group for organizing contacts (e.g. "Work", "Family").
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_groups",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=300, blank=True)
    contacts = models.ManyToManyField(Contact, blank=True, related_name="groups")
    color = models.CharField(max_length=7, default="#3B82F6", help_text="Hex color code")

    class Meta:
        db_table = "contacts_group"
        unique_together = ["user", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.contacts.count()} contacts)"

    @property
    def member_count(self):
        return self.contacts.count()


class BlockedUser(TimeStampedMixin):
    """
    Tracks blocked users. A blocked user cannot send messages,
    view presence, or add the blocker as a contact.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_users",
        help_text="The user who blocked someone.",
    )
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by",
        help_text="The user who was blocked.",
    )
    reason = models.TextField(max_length=500, blank=True)

    class Meta:
        db_table = "contacts_blocked"
        unique_together = ["user", "blocked_user"]

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"

    @staticmethod
    def is_blocked(user, target_user):
        return BlockedUser.objects.filter(user=user, blocked_user=target_user).exists()
