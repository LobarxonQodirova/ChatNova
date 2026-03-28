"""
Serializers for user authentication, registration, and profile management.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation."""

    password = serializers.CharField(
        write_only=True, min_length=8, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "password_confirm",
            "display_name", "phone_number",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError("This username is already taken.")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        return value.lower()

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile settings."""

    class Meta:
        model = UserProfile
        fields = [
            "date_of_birth", "location", "website", "language",
            "timezone", "message_preview", "read_receipts", "typing_indicators",
        ]


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with nested profile."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "display_name", "avatar",
            "bio", "phone_number", "status", "custom_status",
            "last_seen", "email_notifications", "push_notifications",
            "sound_enabled", "theme", "is_verified", "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "email", "date_joined", "is_verified", "last_seen"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""

    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "display_name", "avatar", "bio", "phone_number",
            "custom_status", "email_notifications", "push_notifications",
            "sound_enabled", "theme", "profile",
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data and hasattr(instance, "profile"):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, min_length=8, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        return data


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for embedding in other resources."""

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "avatar", "status"]
        read_only_fields = fields
