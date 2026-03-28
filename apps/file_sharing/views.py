"""
Views for file upload and download.
"""
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, parsers, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.media.models import UploadedFile
from apps.media.services import FileUploadService


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files."""

    file_url = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    human_readable_size = serializers.ReadOnlyField()

    class Meta:
        model = UploadedFile
        fields = [
            "id", "original_filename", "content_type", "file_size",
            "file_url", "thumbnail", "width", "height", "duration",
            "is_image", "human_readable_size", "status", "created_at",
        ]
        read_only_fields = fields


class FileUploadView(APIView):
    """Upload a file. Validates type and size before saving."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": {"code": "validation", "message": "No file provided."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uploaded = FileUploadService.upload_file(request.user, file)
            return Response(
                UploadedFileSerializer(uploaded).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": {"code": "upload_failed", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FileDownloadView(APIView):
    """Download a file by its ID."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id):
        uploaded = get_object_or_404(UploadedFile, id=file_id)
        if not uploaded.file:
            return Response(
                {"error": {"code": "not_found", "message": "File not available."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        response = FileResponse(uploaded.file.open("rb"), content_type=uploaded.content_type)
        response["Content-Disposition"] = f'attachment; filename="{uploaded.original_filename}"'
        return response


class UserFilesView(generics.ListAPIView):
    """List all files uploaded by the current user."""

    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(
            uploader=self.request.user
        ).order_by("-created_at")
