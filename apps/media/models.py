"""
Models for uploaded media files.
"""
import uuid

from django.conf import settings
from django.db import models

from utils.mixins import TimeStampedMixin


class UploadedFile(TimeStampedMixin):
    """
    Generic file upload model. Tracks all files uploaded to the system
    with metadata, virus scan status, and processing state.
    """

    STATUS_CHOICES = [
        ("pending", "Pending Processing"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Processing Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_files",
    )
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveBigIntegerField(help_text="File size in bytes")
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")

    # Image/video-specific fields
    thumbnail = models.ImageField(upload_to="thumbnails/%Y/%m/%d/", blank=True, null=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")

    class Meta:
        db_table = "media_uploaded_file"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uploader", "-created_at"]),
            models.Index(fields=["content_type"]),
        ]

    def __str__(self):
        return self.original_filename

    @property
    def file_url(self):
        return self.file.url if self.file else None

    @property
    def is_image(self):
        return self.content_type.startswith("image/")

    @property
    def is_video(self):
        return self.content_type.startswith("video/")

    @property
    def is_audio(self):
        return self.content_type.startswith("audio/")

    @property
    def human_readable_size(self):
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
