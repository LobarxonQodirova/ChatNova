"""
WebSocket consumer for online presence tracking.
Users connect to a global presence channel to broadcast and receive
online/offline/away status updates for their contacts.
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()


class PresenceConsumer(AsyncJsonWebsocketConsumer):
    """
    Global presence channel. Each user subscribes to updates for their contacts.
    """

    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())

        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.presence_group = "presence_global"
        self.user_group = f"presence_{self.user.id}"

        # Join global presence group and personal group
        await self.channel_layer.group_add(self.presence_group, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        # Set user online and notify contacts
        await self.set_user_status("online")
        await self.broadcast_status("online")

        # Send current online contacts list
        online_contacts = await self.get_online_contacts()
        await self.send_json({
            "type": "online_users",
            "users": online_contacts,
        })

        logger.info(f"Presence connected: {self.user.username}")

    async def disconnect(self, close_code):
        if hasattr(self, "user") and self.user.is_authenticated:
            await self.set_user_status("offline")
            await self.broadcast_status("offline")

        if hasattr(self, "presence_group"):
            await self.channel_layer.group_discard(self.presence_group, self.channel_name)
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")

        if msg_type == "status_update":
            new_status = content.get("status", "online")
            custom_status = content.get("custom_status", "")
            if new_status in ("online", "away", "dnd"):
                await self.set_user_status(new_status, custom_status)
                await self.broadcast_status(new_status, custom_status)

        elif msg_type == "heartbeat":
            # Client sends periodic heartbeats to confirm they're still connected
            await self.set_user_last_seen()
            await self.send_json({"type": "heartbeat_ack"})

    async def broadcast_status(self, status, custom_status=""):
        """Notify all connected clients about a user's status change."""
        await self.channel_layer.group_send(
            self.presence_group,
            {
                "type": "presence_update",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "display_name": str(self.user),
                "avatar": self.user.avatar_url,
                "status": status,
                "custom_status": custom_status,
            },
        )

    async def presence_update(self, event):
        """Receive a presence update and forward it to the WebSocket client."""
        # Don't send users their own status updates
        if event["user_id"] != str(self.user.id):
            # Only send updates for contacts
            is_contact = await self.is_contact(event["user_id"])
            if is_contact:
                await self.send_json({
                    "type": "presence_update",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "display_name": event["display_name"],
                    "avatar": event.get("avatar"),
                    "status": event["status"],
                    "custom_status": event.get("custom_status", ""),
                })

    @database_sync_to_async
    def set_user_status(self, status, custom_status=""):
        from django.utils import timezone

        self.user.status = status
        self.user.last_seen = timezone.now()
        fields = ["status", "last_seen"]
        if custom_status is not None:
            self.user.custom_status = custom_status
            fields.append("custom_status")
        self.user.save(update_fields=fields)

    @database_sync_to_async
    def set_user_last_seen(self):
        from django.utils import timezone

        self.user.last_seen = timezone.now()
        self.user.save(update_fields=["last_seen"])

    @database_sync_to_async
    def get_online_contacts(self):
        from apps.contacts.models import Contact

        contact_user_ids = Contact.objects.filter(
            user=self.user, status="accepted"
        ).values_list("contact_user_id", flat=True)

        online_users = User.objects.filter(
            id__in=contact_user_ids, status__in=["online", "away", "dnd"]
        ).values("id", "username", "display_name", "status", "custom_status")

        return [
            {
                "user_id": str(u["id"]),
                "username": u["username"],
                "display_name": u["display_name"] or u["username"],
                "status": u["status"],
                "custom_status": u["custom_status"],
            }
            for u in online_users
        ]

    @database_sync_to_async
    def is_contact(self, user_id):
        from apps.contacts.models import Contact

        return Contact.objects.filter(
            user=self.user, contact_user_id=user_id, status="accepted"
        ).exists()
