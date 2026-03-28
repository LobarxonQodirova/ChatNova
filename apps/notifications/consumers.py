"""
WebSocket consumer for real-time notification delivery.
Each authenticated user connects to their personal notification channel.
"""
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Personal notification channel for each user.
    Delivers real-time notifications without polling.
    """

    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())

        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.notification_group = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(
            self.notification_group, self.channel_name
        )
        await self.accept()

        # Send unread count on connect
        unread_count = await self.get_unread_count()
        await self.send_json({
            "type": "unread_count",
            "count": unread_count,
        })

        logger.info(f"User {self.user.username} connected to notifications")

    async def disconnect(self, close_code):
        if hasattr(self, "notification_group"):
            await self.channel_layer.group_discard(
                self.notification_group, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")

        if msg_type == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self.mark_notification_read(notification_id)
                unread_count = await self.get_unread_count()
                await self.send_json({
                    "type": "unread_count",
                    "count": unread_count,
                })

        elif msg_type == "mark_all_read":
            await self.mark_all_read()
            await self.send_json({
                "type": "unread_count",
                "count": 0,
            })

    async def notification(self, event):
        """Handle notification sent from Celery task via channel layer."""
        await self.send_json({
            "type": "notification",
            "data": event["data"],
        })
        unread_count = await self.get_unread_count()
        await self.send_json({
            "type": "unread_count",
            "count": unread_count,
        })

    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification

        return Notification.unread_count(self.user)

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification

        try:
            notification = Notification.objects.get(
                id=notification_id, recipient=self.user
            )
            notification.mark_as_read()
        except Notification.DoesNotExist:
            pass

    @database_sync_to_async
    def mark_all_read(self):
        from .services import NotificationService

        NotificationService.mark_all_read(self.user)
