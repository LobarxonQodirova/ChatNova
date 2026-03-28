"""
Admin configuration for conversations, messages, and related models.
"""
from django.contrib import admin

from .models import (
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageReaction,
    ReadReceipt,
)


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 0
    readonly_fields = ["joined_at"]
    raw_id_fields = ["user"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "member_count", "last_activity", "is_archived"]
    list_filter = ["type", "is_archived", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "last_activity"]
    raw_id_fields = ["creator", "pinned_message", "last_message"]
    inlines = [ConversationMemberInline]
    date_hierarchy = "created_at"


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ["file_size", "file_type"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "sender", "conversation", "type", "is_edited", "is_deleted", "created_at"]
    list_filter = ["type", "is_edited", "is_deleted", "created_at"]
    search_fields = ["content", "sender__username"]
    readonly_fields = ["id", "created_at", "updated_at", "edited_at"]
    raw_id_fields = ["sender", "conversation", "parent_message", "forwarded_from"]
    inlines = [MessageAttachmentInline]
    date_hierarchy = "created_at"


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ["user", "emoji", "message", "created_at"]
    list_filter = ["emoji", "created_at"]
    raw_id_fields = ["message", "user"]


@admin.register(ReadReceipt)
class ReadReceiptAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "read_at"]
    list_filter = ["read_at"]
    raw_id_fields = ["message", "user"]
