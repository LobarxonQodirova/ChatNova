"""
Celery tasks for notification processing and delivery.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, notification_id):
    """
    Send a push notification via WebSocket channel layer.
    Falls back to email if the user is offline.
    """
    from .models import Notification

    try:
        notification = Notification.objects.select_related(
            "recipient", "sender"
        ).get(id=notification_id)

        user = notification.recipient

        # Send via WebSocket channel layer
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "notification",
                "data": {
                    "id": str(notification.id),
                    "type": notification.type,
                    "title": notification.title,
                    "body": notification.body,
                    "sender": notification.sender.username if notification.sender else None,
                    "target_type": notification.target_type,
                    "target_id": str(notification.target_id) if notification.target_id else None,
                    "action_url": notification.action_url,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )
        logger.info(f"Push notification sent to {user.username}: {notification.title}")

    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found.")
    except Exception as exc:
        logger.error(f"Failed to send notification {notification_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_email_notification(self, notification_id):
    """Send an email notification for important events."""
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(
            id=notification_id
        )
        user = notification.recipient

        if not user.email_notifications or not user.email:
            return

        subject = f"ChatNova: {notification.title}"
        message = notification.body or notification.title

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email notification sent to {user.email}")

    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found for email.")
    except Exception as exc:
        logger.error(f"Failed to send email notification: {exc}")
        self.retry(exc=exc)


@shared_task
def cleanup_old_notifications():
    """Remove notifications older than 30 days that have been read."""
    from .models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(
        is_read=True, created_at__lt=cutoff
    ).delete()
    logger.info(f"Cleaned up {deleted_count} old notifications.")


@shared_task
def send_batch_digest():
    """
    Send a digest email to users who have unread notifications
    and haven't been online in the last hour.
    """
    from .models import Notification

    one_hour_ago = timezone.now() - timedelta(hours=1)

    users_with_unread = (
        User.objects.filter(
            notifications__is_read=False,
            email_notifications=True,
            last_seen__lt=one_hour_ago,
        )
        .distinct()
    )

    for user in users_with_unread:
        unread = Notification.objects.filter(
            recipient=user, is_read=False
        ).order_by("-created_at")[:10]

        if not unread.exists():
            continue

        count = unread.count()
        summary = "\n".join(
            [f"- {n.title}: {n.body[:80]}" for n in unread[:5]]
        )
        subject = f"ChatNova: You have {count} unread notification(s)"
        message = f"Hi {user.username},\n\nYou have {count} unread notifications:\n\n{summary}\n\nLog in to ChatNova to see more."

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as exc:
            logger.error(f"Failed digest for {user.email}: {exc}")
