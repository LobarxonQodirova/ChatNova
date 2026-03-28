"""
Admin configuration for the accounts app.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = [
        "username", "email", "display_name", "status",
        "is_verified", "is_active", "date_joined",
    ]
    list_filter = ["status", "is_verified", "is_active", "is_staff", "date_joined"]
    search_fields = ["username", "email", "display_name"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "ChatNova Fields",
            {
                "fields": (
                    "display_name", "avatar", "bio", "phone_number",
                    "status", "custom_status", "last_seen",
                    "email_notifications", "push_notifications",
                    "sound_enabled", "theme", "is_verified",
                ),
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Additional Info",
            {
                "fields": ("email", "display_name"),
            },
        ),
    )
