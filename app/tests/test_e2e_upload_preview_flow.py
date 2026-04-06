"""
End-to-end API tests for real upload + preview flows.
"""
from io import BytesIO

from django.urls import reverse
from PIL import Image

from tests.base import BaseAPITestCase
from templates.models import Content, Layer, Widget


class UploadPreviewE2ETests(BaseAPITestCase):
    """Exercise real multipart upload and preview URL generation."""

    def _make_image_file(self, filename="e2e-image.jpg"):
        image = Image.new("RGB", (320, 200), color="blue")
        file_obj = BytesIO()
        image.save(file_obj, format="JPEG")
        file_obj.name = filename
        file_obj.seek(0)
        return file_obj

    def test_upload_then_preview_returns_valid_payload(self):
        template = self.create_template(name="E2E Template")
        layer = Layer.objects.create(
            name="E2E Layer",
            template=template,
            width=1920,
            height=1080,
            x=0,
            y=0,
        )
        widget = Widget.objects.create(
            name="E2E Widget",
            type="image",
            layer=layer,
            x=0,
            y=0,
            width=600,
            height=400,
            z_index=0,
        )
        content = Content.objects.create(
            name="E2E Content",
            type="image",
            widget=widget,
            is_active=True,
        )

        upload_url = reverse("content-upload", kwargs={"id": str(content.id)})
        image_file = self._make_image_file()
        upload_response = self.client.post(upload_url, {"file": image_file}, format="multipart")

        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(upload_response.data.get("status"), "success")
        self.assertEqual(upload_response.data.get("content_id"), str(content.id))

        content.refresh_from_db()
        self.assertTrue(content.file_url)
        self.assertTrue(content.file_size and content.file_size > 0)
        self.assertTrue(content.file_hash)

        preview_url = reverse("content-preview", kwargs={"id": str(content.id)})
        preview_response = self.client.get(preview_url)

        self.assertEqual(preview_response.status_code, 200)
        self.assertEqual(preview_response.data.get("status"), "success")
        self.assertEqual(preview_response.data.get("content_id"), str(content.id))
        self.assertEqual(preview_response.data.get("content_type"), "image")
        preview_url = preview_response.data.get("preview_url")
        self.assertTrue(preview_url)
        self.assertTrue(
            preview_url.startswith("http://")
            or preview_url.startswith("https://")
            or preview_url.startswith("/media/")
        )
