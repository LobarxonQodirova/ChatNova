"""
Views for contact management, contact groups, and user blocking.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BlockedUser, Contact, ContactGroup
from .serializers import (
    BlockedUserSerializer,
    BlockUserSerializer,
    ContactCreateSerializer,
    ContactGroupCreateSerializer,
    ContactGroupSerializer,
    ContactSerializer,
    ContactUpdateSerializer,
)


class ContactListCreateView(generics.ListCreateAPIView):
    """List all contacts or send a new contact request."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ContactCreateSerializer
        return ContactSerializer

    def get_queryset(self):
        queryset = Contact.objects.filter(
            user=self.request.user
        ).select_related("contact_user")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        favorites = self.request.query_params.get("favorites")
        if favorites and favorites.lower() == "true":
            queryset = queryset.filter(is_favorite=True)

        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(contact_user__username__icontains=search)
                | Q(contact_user__display_name__icontains=search)
                | Q(nickname__icontains=search)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = ContactCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        return Response(
            ContactSerializer(contact).data,
            status=status.HTTP_201_CREATED,
        )


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or remove a contact."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ContactUpdateSerializer
        return ContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(
            user=self.request.user
        ).select_related("contact_user")


class ContactRequestsView(generics.ListAPIView):
    """List pending contact requests received by the current user."""

    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(
            contact_user=self.request.user, status="pending"
        ).select_related("user")


class ContactRequestResponseView(APIView):
    """Accept or decline a pending contact request."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, contact_id):
        contact = get_object_or_404(
            Contact, id=contact_id, contact_user=request.user, status="pending"
        )
        action = request.data.get("action")

        if action == "accept":
            contact.accept()
            return Response(
                {"message": "Contact request accepted."},
                status=status.HTTP_200_OK,
            )
        elif action == "decline":
            contact.decline()
            return Response(
                {"message": "Contact request declined."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": {"code": "validation", "message": "Action must be 'accept' or 'decline'."}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ContactGroupListCreateView(generics.ListCreateAPIView):
    """List or create contact groups."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ContactGroupCreateSerializer
        return ContactGroupSerializer

    def get_queryset(self):
        return ContactGroup.objects.filter(
            user=self.request.user
        ).prefetch_related("contacts__contact_user")

    def perform_create(self, serializer):
        serializer.save()


class ContactGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a contact group."""

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ContactGroupCreateSerializer
        return ContactGroupSerializer

    def get_queryset(self):
        return ContactGroup.objects.filter(
            user=self.request.user
        ).prefetch_related("contacts__contact_user")


class BlockedUserListView(generics.ListCreateAPIView):
    """List blocked users or block a new user."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BlockUserSerializer
        return BlockedUserSerializer

    def get_queryset(self):
        return BlockedUser.objects.filter(
            user=self.request.user
        ).select_related("blocked_user")

    def create(self, request, *args, **kwargs):
        serializer = BlockUserSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        blocked = serializer.save()
        return Response(
            BlockedUserSerializer(blocked).data,
            status=status.HTTP_201_CREATED,
        )


class UnblockUserView(APIView):
    """Unblock a previously blocked user."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        blocked = get_object_or_404(
            BlockedUser, user=request.user, blocked_user_id=user_id
        )
        blocked.delete()
        return Response(
            {"message": "User unblocked."},
            status=status.HTTP_204_NO_CONTENT,
        )
