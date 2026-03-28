"""
Serializers for contacts, contact groups, and blocked users.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserMinimalSerializer

from .models import BlockedUser, Contact, ContactGroup

User = get_user_model()


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for displaying contact details."""

    contact_user = UserMinimalSerializer(read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id", "contact_user", "nickname", "status",
            "is_favorite", "notes", "groups", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class ContactCreateSerializer(serializers.Serializer):
    """Serializer for adding a new contact / sending a contact request."""

    contact_user_id = serializers.UUIDField()
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_contact_user_id(self, value):
        request_user = self.context["request"].user
        if str(value) == str(request_user.id):
            raise serializers.ValidationError("You cannot add yourself as a contact.")

        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("User not found.")

        if Contact.objects.filter(user=request_user, contact_user_id=value).exists():
            raise serializers.ValidationError("This user is already in your contacts.")

        if BlockedUser.is_blocked(User.objects.get(id=value), request_user):
            raise serializers.ValidationError("Cannot add this user.")

        return value

    def create(self, validated_data):
        return Contact.objects.create(
            user=self.context["request"].user,
            contact_user_id=validated_data["contact_user_id"],
            nickname=validated_data.get("nickname", ""),
            notes=validated_data.get("notes", ""),
        )


class ContactUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating contact details."""

    class Meta:
        model = Contact
        fields = ["nickname", "is_favorite", "notes"]


class ContactGroupSerializer(serializers.ModelSerializer):
    """Serializer for contact groups."""

    member_count = serializers.ReadOnlyField()
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = ContactGroup
        fields = [
            "id", "name", "description", "color",
            "contacts", "member_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ContactGroupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a contact group."""

    contact_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False
    )

    class Meta:
        model = ContactGroup
        fields = ["name", "description", "color", "contact_ids"]

    def validate_name(self, value):
        user = self.context["request"].user
        existing = ContactGroup.objects.filter(user=user, name=value)
        if self.instance:
            existing = existing.exclude(id=self.instance.id)
        if existing.exists():
            raise serializers.ValidationError("You already have a group with this name.")
        return value

    def create(self, validated_data):
        contact_ids = validated_data.pop("contact_ids", [])
        group = ContactGroup.objects.create(
            user=self.context["request"].user, **validated_data
        )
        if contact_ids:
            contacts = Contact.objects.filter(
                id__in=contact_ids, user=self.context["request"].user
            )
            group.contacts.set(contacts)
        return group

    def update(self, instance, validated_data):
        contact_ids = validated_data.pop("contact_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if contact_ids is not None:
            contacts = Contact.objects.filter(
                id__in=contact_ids, user=self.context["request"].user
            )
            instance.contacts.set(contacts)
        return instance


class BlockedUserSerializer(serializers.ModelSerializer):
    """Serializer for blocked users."""

    blocked_user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = BlockedUser
        fields = ["id", "blocked_user", "reason", "created_at"]
        read_only_fields = ["id", "created_at"]


class BlockUserSerializer(serializers.Serializer):
    """Serializer for blocking a user."""

    user_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_user_id(self, value):
        request_user = self.context["request"].user
        if str(value) == str(request_user.id):
            raise serializers.ValidationError("You cannot block yourself.")
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("User not found.")
        if BlockedUser.objects.filter(user=request_user, blocked_user_id=value).exists():
            raise serializers.ValidationError("User is already blocked.")
        return value

    def create(self, validated_data):
        request_user = self.context["request"].user
        blocked = BlockedUser.objects.create(
            user=request_user,
            blocked_user_id=validated_data["user_id"],
            reason=validated_data.get("reason", ""),
        )
        # Remove from contacts if exists
        Contact.objects.filter(
            user=request_user, contact_user_id=validated_data["user_id"]
        ).delete()
        Contact.objects.filter(
            user_id=validated_data["user_id"], contact_user=request_user
        ).delete()
        return blocked
