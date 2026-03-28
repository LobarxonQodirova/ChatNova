"""
WebSocket consumers for real-time chat functionality.
Handles message delivery, typing indicators, read receipts,
and online presence within conversations.
"""
import json
import logging
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for individual conversation rooms.
    Supports: messages, typing indicators, read receipts, reactions.
    """

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope.get("user", AnonymousUser())

        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify membership
        is_member = await self.check_membership()
        if not is_member:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_join",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "display_name": str(self.user),
            },
        )

        # Update user presence
        await self.set_user_online()
        logger.info(f"User {self.user.username} connected to conversation {self.conversation_id}")

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_leave",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                },
            )
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        logger.info(f"User disconnected from conversation {getattr(self, 'conversation_id', 'unknown')}")

    async def receive_json(self, content, **kwargs):
        """Route incoming WebSocket messages to the appropriate handler."""
        msg_type = content.get("type", "")

        handlers = {
            "chat_message": self.handle_chat_message,
            "typing_start": self.handle_typing_start,
            "typing_stop": self.handle_typing_stop,
            "mark_read": self.handle_mark_read,
            "reaction": self.handle_reaction,
            "message_edit": self.handle_message_edit,
            "message_delete": self.handle_message_delete,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(content)
        else:
            await self.send_json({
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            })

    async def handle_chat_message(self, content):
        """Save and broadcast a new chat message."""
        message_content = content.get("content", "").strip()
        message_type = content.get("message_type", "text")
        parent_id = content.get("parent_message_id")

        if not message_content:
            await self.send_json({
                "type": "error",
                "message": "Message content cannot be empty.",
            })
            return

        message_data = await self.save_message(
            message_content, message_type, parent_id
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_data,
            },
        )

    async def handle_typing_start(self, content):
        """Broadcast that a user started typing."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "display_name": str(self.user),
                "is_typing": True,
            },
        )

    async def handle_typing_stop(self, content):
        """Broadcast that a user stopped typing."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "display_name": str(self.user),
                "is_typing": False,
            },
        )

    async def handle_mark_read(self, content):
        """Mark messages as read and notify other participants."""
        message_id = content.get("message_id")
        if message_id:
            await self.mark_message_read(message_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "message_id": message_id,
                    "read_at": datetime.utcnow().isoformat(),
                },
            )

    async def handle_reaction(self, content):
        """Add or remove an emoji reaction."""
        message_id = content.get("message_id")
        emoji = content.get("emoji")
        if message_id and emoji:
            result = await self.toggle_reaction(message_id, emoji)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_reaction",
                    "message_id": message_id,
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "emoji": emoji,
                    "action": result,
                },
            )

    async def handle_message_edit(self, content):
        """Edit an existing message."""
        message_id = content.get("message_id")
        new_content = content.get("content", "").strip()
        if message_id and new_content:
            success = await self.edit_message(message_id, new_content)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_edited",
                        "message_id": message_id,
                        "content": new_content,
                        "edited_by": str(self.user.id),
                        "edited_at": datetime.utcnow().isoformat(),
                    },
                )

    async def handle_message_delete(self, content):
        """Soft-delete a message."""
        message_id = content.get("message_id")
        if message_id:
            success = await self.delete_message(message_id)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_deleted",
                        "message_id": message_id,
                        "deleted_by": str(self.user.id),
                    },
                )

    # ----- Group send handlers (broadcast to all clients in room) -----

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat_message",
            "message": event["message"],
        })

    async def typing_indicator(self, event):
        # Don't send typing indicator back to the sender
        if event["user_id"] != str(self.user.id):
            await self.send_json({
                "type": "typing_indicator",
                "user_id": event["user_id"],
                "username": event["username"],
                "display_name": event["display_name"],
                "is_typing": event["is_typing"],
            })

    async def read_receipt(self, event):
        await self.send_json({
            "type": "read_receipt",
            "user_id": event["user_id"],
            "username": event["username"],
            "message_id": event["message_id"],
            "read_at": event["read_at"],
        })

    async def message_reaction(self, event):
        await self.send_json({
            "type": "message_reaction",
            "message_id": event["message_id"],
            "user_id": event["user_id"],
            "username": event["username"],
            "emoji": event["emoji"],
            "action": event["action"],
        })

    async def message_edited(self, event):
        await self.send_json({
            "type": "message_edited",
            "message_id": event["message_id"],
            "content": event["content"],
            "edited_by": event["edited_by"],
            "edited_at": event["edited_at"],
        })

    async def message_deleted(self, event):
        await self.send_json({
            "type": "message_deleted",
            "message_id": event["message_id"],
            "deleted_by": event["deleted_by"],
        })

    async def user_join(self, event):
        await self.send_json({
            "type": "user_join",
            "user_id": event["user_id"],
            "username": event["username"],
            "display_name": event["display_name"],
        })

    async def user_leave(self, event):
        await self.send_json({
            "type": "user_leave",
            "user_id": event["user_id"],
            "username": event["username"],
        })

    # ----- Database operations -----

    @database_sync_to_async
    def check_membership(self):
        from apps.conversations.models import ConversationMember

        return ConversationMember.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
            is_active=True,
        ).exists()

    @database_sync_to_async
    def set_user_online(self):
        self.user.set_online()

    @database_sync_to_async
    def save_message(self, content, msg_type, parent_id):
        from apps.conversations.models import Conversation, Message

        conversation = Conversation.objects.get(id=self.conversation_id)
        kwargs = {
            "conversation": conversation,
            "sender": self.user,
            "content": content,
            "type": msg_type,
        }
        if parent_id:
            try:
                kwargs["parent_message"] = Message.objects.get(id=parent_id)
            except Message.DoesNotExist:
                pass

        message = Message.objects.create(**kwargs)
        conversation.last_message = message
        conversation.save(update_fields=["last_message", "last_activity"])

        return {
            "id": str(message.id),
            "conversation_id": str(conversation.id),
            "sender": {
                "id": str(self.user.id),
                "username": self.user.username,
                "display_name": str(self.user),
                "avatar": self.user.avatar_url,
            },
            "content": message.content,
            "type": message.type,
            "parent_message_id": str(message.parent_message_id) if message.parent_message_id else None,
            "created_at": message.created_at.isoformat(),
        }

    @database_sync_to_async
    def mark_message_read(self, message_id):
        from apps.conversations.models import ConversationMember, Message, ReadReceipt

        try:
            message = Message.objects.get(id=message_id)
            ReadReceipt.objects.get_or_create(message=message, user=self.user)
            ConversationMember.objects.filter(
                conversation=message.conversation, user=self.user
            ).update(last_read_at=message.created_at)
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def toggle_reaction(self, message_id, emoji):
        from apps.conversations.models import Message, MessageReaction

        try:
            message = Message.objects.get(id=message_id)
            reaction, created = MessageReaction.objects.get_or_create(
                message=message, user=self.user, emoji=emoji,
            )
            if not created:
                reaction.delete()
                return "removed"
            return "added"
        except Message.DoesNotExist:
            return "error"

    @database_sync_to_async
    def edit_message(self, message_id, new_content):
        from apps.conversations.models import Message

        try:
            message = Message.objects.get(id=message_id, sender=self.user)
            message.edit_message(new_content)
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_message(self, message_id):
        from apps.conversations.models import Message

        try:
            message = Message.objects.get(id=message_id, sender=self.user)
            message.soft_delete()
            return True
        except Message.DoesNotExist:
            return False
