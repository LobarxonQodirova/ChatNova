"""URL patterns for file sharing."""
from django.urls import path

from . import views

app_name = "file_sharing"

urlpatterns = [
    path("", views.FileUploadView.as_view(), name="upload"),
    path("mine/", views.UserFilesView.as_view(), name="my-files"),
    path("<uuid:file_id>/", views.FileDownloadView.as_view(), name="download"),
]
