"""
Views for group management, membership, messages, and settings.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.pagination import MessageCursorPagination

from .models import Group, GroupMember, GroupMessage, GroupSettings
from .serializers import (
    GroupCreateSerializer,
    GroupMemberSerializer,
    GroupMessageCreateSerializer,
    GroupMessageSerializer,
    GroupSerializer,
    GroupSettingsSerializer,
)

User = get_user_model()


class GroupListCreateView(generics.ListCreateAPIView):
    """List user's groups or create a new one."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupCreateSerializer
        return GroupSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Group.objects.filter(
            members__user=user, members__is_active=True, is_active=True
        ).select_related("creator", "settings").distinct()

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-last_activity")

    def create(self, request, *args, **kwargs):
        serializer = GroupCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(
            GroupSerializer(group, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or deactivate a group."""

    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Group.objects.filter(
            members__user=self.request.user,
            members__is_active=True,
            is_active=True,
        ).select_related("creator", "settings")

    def perform_update(self, serializer):
        group = self.get_object()
        membership = get_object_or_404(
            GroupMember, group=group, user=self.request.user, is_active=True
        )
        if group.settings.only_admins_can_edit_info and not membership.can_admin:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only admins can edit group info.")
        serializer.save()

    def perform_destroy(self, instance):
        membership = get_object_or_404(
            GroupMember, group=instance, user=self.request.user, is_active=True
        )
        if membership.role != "owner":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only the group owner can delete the group.")
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class GroupPublicSearchView(generics.ListAPIView):
    """Search for public groups."""

    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Group.objects.none()
        return Group.objects.filter(
            is_public=True, is_active=True,
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).select_related("creator")[:20]


class GroupMembersView(APIView):
    """List members or add a new member to a group."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(
            Group, id=group_id,
            members__user=request.user,
            members__is_active=True,
        )
        members = group.members.filter(is_active=True).select_related("user")
        serializer = GroupMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id, is_active=True)
        membership = get_object_or_404(
            GroupMember, group=group, user=request.user, is_active=True
        )

        if not membership.can_manage and not group.settings.member_can_invite:
            return Response(
                {"error": {"code": "forbidden", "message": "You don't have permission to add members."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": {"code": "validation", "message": "user_id is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=user_id, is_active=True)
        try:
            member = group.add_member(user)
        except ValueError as e:
            return Response(
                {"error": {"code": "capacity", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GroupMessage.objects.create(
            group=group, sender=request.user,
            content=f"{user.username} was added to the group.",
            type="system",
        )

        return Response(
            GroupMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class GroupMemberDetailView(APIView):
    """Update role, kick, or leave a group."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, group_id, member_id):
        """Update a member's role or mute status."""
        group = get_object_or_404(Group, id=group_id, is_active=True)
        requester = get_object_or_404(
            GroupMember, group=group, user=request.user, is_active=True
        )
        target = get_object_or_404(GroupMember, id=member_id, group=group, is_active=True)

        if not requester.can_admin:
            return Response(
                {"error": {"code": "forbidden", "message": "Only admins can update member roles."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_role = request.data.get("role")
        if new_role:
            if new_role == "owner" and requester.role != "owner":
                return Response(
                    {"error": {"code": "forbidden", "message": "Only the owner can transfer ownership."}},
                    status=status.HTTP_403_FORBIDDEN,
                )
            target.role = new_role
            target.save(update_fields=["role"])

        is_muted = request.data.get("is_muted")
        if is_muted is not None:
            target.is_muted = is_muted
            target.save(update_fields=["is_muted"])

        return Response(GroupMemberSerializer(target).data)

    def delete(self, request, group_id, member_id):
        """Remove a member from the group."""
        group = get_object_or_404(Group, id=group_id, is_active=True)
        requester = get_object_or_404(
            GroupMember, group=group, user=request.user, is_active=True
        )
        target = get_object_or_404(GroupMember, id=member_id, group=group, is_active=True)

        # Self-leave
        if target.user_id == request.user.id:
            if target.role == "owner":
                return Response(
                    {"error": {"code": "forbidden", "message": "Transfer ownership before leaving."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            group.remove_member(request.user)
            GroupMessage.objects.create(
                group=group, sender=request.user,
                content=f"{request.user.username} left the group.",
                type="system",
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Kick another member
        if not requester.can_admin:
            return Response(
                {"error": {"code": "forbidden", "message": "Only admins can remove members."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        group.remove_member(target.user)
        GroupMessage.objects.create(
            group=group, sender=request.user,
            content=f"{target.user.username} was removed from the group.",
            type="system",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupMessageListCreateView(generics.ListCreateAPIView):
    """List or send messages in a group."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupMessageCreateSerializer
        return GroupMessageSerializer

    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        get_object_or_404(
            GroupMember, group_id=group_id, user=self.request.user, is_active=True
        )
        return (
            GroupMessage.objects.filter(group_id=group_id, is_deleted=False)
            .select_related("sender", "reply_to__sender")
        )

    def perform_create(self, serializer):
        group_id = self.kwargs["group_id"]
        group = get_object_or_404(Group, id=group_id, is_active=True)
        membership = get_object_or_404(
            GroupMember, group=group, user=self.request.user, is_active=True
        )

        if group.settings.only_admins_can_post and not membership.can_manage:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only admins can post in this group.")

        message = serializer.save(sender=self.request.user, group=group)
        group.last_activity = message.created_at
        group.save(update_fields=["last_activity"])


class GroupSettingsView(generics.RetrieveUpdateAPIView):
    """View or update group settings."""

    serializer_class = GroupSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        group_id = self.kwargs["group_id"]
        group = get_object_or_404(Group, id=group_id, is_active=True)
        get_object_or_404(
            GroupMember, group=group, user=self.request.user, is_active=True
        )
        settings_obj, _ = GroupSettings.objects.get_or_create(group=group)
        return settings_obj

    def perform_update(self, serializer):
        group_id = self.kwargs["group_id"]
        membership = get_object_or_404(
            GroupMember, group_id=group_id, user=self.request.user, is_active=True
        )
        if not membership.can_admin:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only admins can update group settings.")
        serializer.save()


class GroupInviteLinkView(APIView):
    """Get or regenerate a group invite link."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id, is_active=True)
        get_object_or_404(
            GroupMember, group=group, user=request.user, is_active=True
        )
        if not group.invite_link:
            group.generate_invite_link()
        return Response({"invite_link": group.invite_link})

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id, is_active=True)
        membership = get_object_or_404(
            GroupMember, group=group, user=request.user, is_active=True
        )
        if not membership.can_admin:
            return Response(
                {"error": {"code": "forbidden", "message": "Only admins can regenerate invite links."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        link = group.generate_invite_link()
        return Response({"invite_link": link})


class GroupJoinView(APIView):
    """Join a group via invite link."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_link = request.data.get("invite_link")
        if not invite_link:
            return Response(
                {"error": {"code": "validation", "message": "invite_link is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = get_object_or_404(Group, invite_link=invite_link, is_active=True)

        if GroupMember.objects.filter(
            group=group, user=request.user, is_active=True
        ).exists():
            return Response(
                {"error": {"code": "conflict", "message": "You are already a member."}},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            member = group.add_member(request.user)
        except ValueError as e:
            return Response(
                {"error": {"code": "capacity", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GroupMessage.objects.create(
            group=group, sender=request.user,
            content=f"{request.user.username} joined the group.",
            type="system",
        )

        return Response(
            GroupSerializer(group, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
