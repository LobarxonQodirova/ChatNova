"""
Service layer for file upload handling, validation, and processing.
"""
import hashlib
import logging
import os
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

from .models import UploadedFile

logger = logging.getLogger(__name__)

# Allowed file types and their extensions
ALLOWED_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    "image/svg+xml": [".svg"],
    "video/mp4": [".mp4"],
    "video/webm": [".webm"],
    "video/quicktime": [".mov"],
    "audio/mpeg": [".mp3"],
    "audio/ogg": [".ogg"],
    "audio/wav": [".wav"],
    "audio/webm": [".weba"],
    "application/pdf": [".pdf"],
    "application/zip": [".zip"],
    "application/x-rar-compressed": [".rar"],
    "text/plain": [".txt"],
    "text/csv": [".csv"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.ms-excel": [".xls"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-powerpoint": [".ppt"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
}

MAX_FILE_SIZE = getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)  # 50MB default
MAX_IMAGE_DIMENSION = 8192
THUMBNAIL_SIZE = (300, 300)


class FileUploadService:
    """Handles file validation, processing, and storage."""

    @staticmethod
    def validate_file(file):
        """
        Validate uploaded file type, size, and extension.

        Args:
            file: Django UploadedFile instance.

        Raises:
            ValidationError: If the file doesn't pass validation.
        """
        # Check file size
        if file.size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f"File size ({file.size / (1024 * 1024):.1f}MB) exceeds "
                f"the maximum allowed size ({max_mb:.0f}MB)."
            )

        # Check content type
        content_type = file.content_type
        if content_type not in ALLOWED_TYPES:
            raise ValidationError(
                f"File type '{content_type}' is not allowed. "
                f"Allowed types: {', '.join(ALLOWED_TYPES.keys())}"
            )

        # Check extension matches content type
        _, ext = os.path.splitext(file.name)
        ext = ext.lower()
        allowed_extensions = ALLOWED_TYPES.get(content_type, [])
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' doesn't match content type '{content_type}'."
            )

        return True

    @staticmethod
    def compute_checksum(file):
        """Compute SHA-256 hash of the file content."""
        sha256 = hashlib.sha256()
        file.seek(0)
        for chunk in file.chunks():
            sha256.update(chunk)
        file.seek(0)
        return sha256.hexdigest()

    @staticmethod
    def generate_thumbnail(file, content_type):
        """
        Generate a thumbnail for image files.

        Args:
            file: Django UploadedFile instance.
            content_type: MIME type string.

        Returns:
            Tuple of (thumbnail_file, width, height) or (None, None, None).
        """
        if not content_type.startswith("image/") or content_type == "image/svg+xml":
            return None, None, None

        try:
            file.seek(0)
            image = Image.open(file)
            width, height = image.size

            # Validate dimensions
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ValidationError(
                    f"Image dimensions ({width}x{height}) exceed "
                    f"maximum ({MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})."
                )

            # Generate thumbnail
            image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            thumb_io = BytesIO()
            image_format = "JPEG" if content_type == "image/jpeg" else "PNG"
            image.save(thumb_io, format=image_format, quality=85)
            thumb_io.seek(0)

            file.seek(0)
            return thumb_io, width, height

        except (IOError, OSError) as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            file.seek(0)
            return None, None, None

    @classmethod
    def upload_file(cls, user, file):
        """
        Full file upload pipeline: validate, compute hash, create thumbnail, save.

        Args:
            user: User instance who is uploading.
            file: Django UploadedFile instance.

        Returns:
            UploadedFile model instance.
        """
        cls.validate_file(file)

        checksum = cls.compute_checksum(file)

        # Check for duplicate
        existing = UploadedFile.objects.filter(
            uploader=user, checksum=checksum, status="ready"
        ).first()
        if existing:
            return existing

        thumbnail, width, height = cls.generate_thumbnail(file, file.content_type)

        uploaded = UploadedFile(
            uploader=user,
            file=file,
            original_filename=file.name,
            content_type=file.content_type or "application/octet-stream",
            file_size=file.size,
            checksum=checksum,
            width=width,
            height=height,
            status="ready",
        )

        if thumbnail:
            from django.core.files.uploadedfile import InMemoryUploadedFile

            thumb_name = f"thumb_{file.name.rsplit('.', 1)[0]}.jpg"
            uploaded.thumbnail = InMemoryUploadedFile(
                file=thumbnail,
                field_name="thumbnail",
                name=thumb_name,
                content_type="image/jpeg",
                size=thumbnail.getbuffer().nbytes,
                charset=None,
            )

        uploaded.save()
        logger.info(
            f"File uploaded: {uploaded.original_filename} "
            f"({uploaded.human_readable_size}) by {user.username}"
        )
        return uploaded

    @staticmethod
    def delete_file(uploaded_file):
        """Delete an uploaded file and its thumbnail from storage."""
        try:
            if uploaded_file.file:
                uploaded_file.file.delete(save=False)
            if uploaded_file.thumbnail:
                uploaded_file.thumbnail.delete(save=False)
            uploaded_file.delete()
            logger.info(f"File deleted: {uploaded_file.original_filename}")
        except Exception as e:
            logger.error(f"Failed to delete file {uploaded_file.id}: {e}")
            raise
