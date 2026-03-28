"""
URL patterns for group management.
"""
from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupListCreateView.as_view(), name="list-create"),
    path("search/", views.GroupPublicSearchView.as_view(), name="search"),
    path("join/", views.GroupJoinView.as_view(), name="join"),
    path("<uuid:id>/", views.GroupDetailView.as_view(), name="detail"),
    path("<uuid:group_id>/members/", views.GroupMembersView.as_view(), name="members"),
    path("<uuid:group_id>/members/<uuid:member_id>/", views.GroupMemberDetailView.as_view(), name="member-detail"),
    path("<uuid:group_id>/messages/", views.GroupMessageListCreateView.as_view(), name="messages"),
    path("<uuid:group_id>/settings/", views.GroupSettingsView.as_view(), name="settings"),
    path("<uuid:group_id>/invite/", views.GroupInviteLinkView.as_view(), name="invite"),
]
