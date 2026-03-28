"""
Service layer for creating and managing notifications.
Provides a clean API for other apps to create notifications.
"""
import logging

from django.contrib.auth import get_user_model

from .models import Notification
from .tasks import send_email_notification, send_push_notification

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Central service for creating and dispatching notifications.
    All notification creation should go through this service.
    """

    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        body="",
        sender=None,
        target_type="",
        target_id=None,
        action_url="",
        send_push=True,
        send_email=False,
    ):
        """
        Create a notification and optionally dispatch push/email delivery.

        Args:
            recipient: User instance who receives the notification.
            notification_type: One of Notification.TYPE_CHOICES.
            title: Short notification title.
            body: Optional longer description.
            sender: Optional User instance who triggered the event.
            target_type: Related object type (e.g., 'conversation').
            target_id: UUID of the related object.
            action_url: Frontend URL to navigate when clicking the notification.
            send_push: Whether to dispatch a push notification task.
            send_email: Whether to dispatch an email notification task.

        Returns:
            The created Notification instance.
        """
        # Don't notify the user about their own actions
        if sender and sender.id == recipient.id:
            return None

        # Check if user has DND status
        if recipient.status == "dnd" and notification_type not in ("system",):
            return None

        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            type=notification_type,
            title=title,
            body=body,
            target_type=target_type,
            target_id=target_id,
            action_url=action_url,
        )

        if send_push and recipient.push_notifications:
            send_push_notification.delay(str(notification.id))

        if send_email and recipient.email_notifications:
            send_email_notification.delay(str(notification.id))

        return notification

    @staticmethod
    def notify_new_message(message):
        """Create notifications for a new message in a conversation."""
        from apps.conversations.models import ConversationMember

        conversation = message.conversation
        members = ConversationMember.objects.filter(
            conversation=conversation, is_active=True, is_muted=False,
        ).exclude(user=message.sender).select_related("user")

        sender_name = str(message.sender) if message.sender else "Someone"
        preview = message.content[:100] if message.content else "[attachment]"

        for member in members:
            NotificationService.create_notification(
                recipient=member.user,
                notification_type="message",
                title=f"New message from {sender_name}",
                body=preview,
                sender=message.sender,
                target_type="conversation",
                target_id=message.conversation_id,
                action_url=f"/chat/{message.conversation_id}",
            )

    @staticmethod
    def notify_mention(message, mentioned_users):
        """Create notifications for users mentioned in a message."""
        sender_name = str(message.sender) if message.sender else "Someone"

        for user in mentioned_users:
            NotificationService.create_notification(
                recipient=user,
                notification_type="mention",
                title=f"{sender_name} mentioned you",
                body=message.content[:100],
                sender=message.sender,
                target_type="conversation",
                target_id=message.conversation_id,
                action_url=f"/chat/{message.conversation_id}",
                send_email=True,
            )

    @staticmethod
    def notify_contact_request(contact):
        """Notify a user about a new contact request."""
        NotificationService.create_notification(
            recipient=contact.contact_user,
            notification_type="contact_request",
            title=f"{contact.user.username} wants to connect",
            body="You have a new contact request.",
            sender=contact.user,
            target_type="contact",
            target_id=contact.id,
            action_url="/contacts/requests",
            send_email=True,
        )

    @staticmethod
    def notify_contact_accepted(contact):
        """Notify a user that their contact request was accepted."""
        NotificationService.create_notification(
            recipient=contact.user,
            notification_type="contact_accepted",
            title=f"{contact.contact_user.username} accepted your request",
            body="You are now connected.",
            sender=contact.contact_user,
            target_type="contact",
            target_id=contact.id,
            action_url=f"/contacts",
        )

    @staticmethod
    def notify_group_invite(group, invited_user, inviter):
        """Notify a user about a group invitation."""
        NotificationService.create_notification(
            recipient=invited_user,
            notification_type="group_invite",
            title=f"Invited to {group.name}",
            body=f"{inviter.username} invited you to join the group.",
            sender=inviter,
            target_type="group",
            target_id=group.id,
            action_url=f"/groups/{group.id}",
        )

    @staticmethod
    def notify_reaction(message, reactor, emoji):
        """Notify a message author about a new reaction."""
        if message.sender and message.sender != reactor:
            NotificationService.create_notification(
                recipient=message.sender,
                notification_type="reaction",
                title=f"{reactor.username} reacted {emoji}",
                body=f'to your message: "{message.content[:60]}"',
                sender=reactor,
                target_type="conversation",
                target_id=message.conversation_id,
                action_url=f"/chat/{message.conversation_id}",
            )

    @staticmethod
    def mark_all_read(user):
        """Mark all notifications as read for a user."""
        from django.utils import timezone

        Notification.objects.filter(
            recipient=user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
