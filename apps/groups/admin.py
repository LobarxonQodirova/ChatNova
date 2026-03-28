"""
Admin configuration for groups.
"""
from django.contrib import admin

from .models import Group, GroupMember, GroupMessage, GroupSettings


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    readonly_fields = ["joined_at"]
    raw_id_fields = ["user"]


class GroupSettingsInline(admin.StackedInline):
    model = GroupSettings
    can_delete = False


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "creator", "member_count", "is_public", "is_active", "last_activity"]
    list_filter = ["is_public", "is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "last_activity", "invite_link"]
    raw_id_fields = ["creator"]
    inlines = [GroupSettingsInline, GroupMemberInline]


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "group", "sender", "type", "is_edited", "is_deleted", "created_at"]
    list_filter = ["type", "is_edited", "is_deleted", "created_at"]
    search_fields = ["content", "sender__username", "group__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["group", "sender", "reply_to"]
    date_hierarchy = "created_at"
