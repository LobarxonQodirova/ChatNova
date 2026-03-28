"""
URL patterns for contacts management.
"""
from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    # Contacts
    path("", views.ContactListCreateView.as_view(), name="list-create"),
    path("<uuid:id>/", views.ContactDetailView.as_view(), name="detail"),
    path("requests/", views.ContactRequestsView.as_view(), name="requests"),
    path("requests/<uuid:contact_id>/respond/", views.ContactRequestResponseView.as_view(), name="respond"),

    # Contact Groups
    path("groups/", views.ContactGroupListCreateView.as_view(), name="group-list-create"),
    path("groups/<uuid:id>/", views.ContactGroupDetailView.as_view(), name="group-detail"),

    # Blocking
    path("blocked/", views.BlockedUserListView.as_view(), name="blocked-list"),
    path("blocked/<uuid:user_id>/", views.UnblockUserView.as_view(), name="unblock"),
]
