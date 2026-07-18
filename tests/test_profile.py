import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="+998905550001")
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def test_patch_name_parts_composes_full_name(self):
        response = self.api.patch(
            "/api/auth/me/",
            {"first_name": "Ali", "last_name": "Valiyev", "birth_date": "1995-04-12"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Ali Valiyev")
        self.assertEqual(str(self.user.birth_date), "1995-04-12")

    def test_avatar_upload_returns_absolute_url(self):
        avatar = SimpleUploadedFile("me.png", _png_bytes(), content_type="image/png")
        response = self.api.patch("/api/auth/me/", {"avatar": avatar}, format="multipart")
        self.assertEqual(response.status_code, 200)
        url = response.json()["user"]["avatar_url"]
        self.assertTrue(url.startswith("http"))
        self.assertIn("/media/avatars/", url)
