"""
URL patterns for authentication and user management.
"""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", views.RefreshTokenView.as_view(), name="token-refresh"),
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    path("password/change/", views.ChangePasswordView.as_view(), name="change-password"),
    path("users/search/", views.UserSearchView.as_view(), name="user-search"),
]
