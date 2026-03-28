"""
Views for user authentication, registration, and profile management.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import IsAccountOwner
from .serializers import (
    ChangePasswordSerializer,
    UserMinimalSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user account."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Authenticate user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """Blacklist the refresh token to log out the user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": {"code": "missing_token", "message": "Refresh token is required."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            request.user.set_offline()
            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"error": {"code": "invalid_token", "message": "Invalid or expired token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RefreshTokenView(TokenRefreshView):
    """Refresh an access token using a valid refresh token."""

    permission_classes = [permissions.AllowAny]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Get or update the currently authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated, IsAccountOwner]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class UserSearchView(generics.ListAPIView):
    """Search for users by username, display name, or email."""

    serializer_class = UserMinimalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return User.objects.none()

        return (
            User.objects.filter(is_active=True)
            .exclude(id=self.request.user.id)
            .filter(
                models__icontains=query,
            )
        )

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return User.objects.none()

        from django.db.models import Q

        return (
            User.objects.filter(is_active=True)
            .exclude(id=self.request.user.id)
            .filter(
                Q(username__icontains=query)
                | Q(display_name__icontains=query)
                | Q(email__icontains=query)
            )[:20]
        )
