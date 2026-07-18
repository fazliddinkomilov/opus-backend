import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User


class ReverseGeocodeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.api = APIClient()
        self.user = User.objects.create_user(phone="+998901234567", full_name="Geo User")
        self.api.force_authenticate(user=self.user)

    def test_reverse_geocode_endpoint_caches_rounded_coordinates(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps({"display_name": "Tashkent, Chilanzar"}).encode("utf-8")

        with patch("apps.geo.services.urlopen", return_value=FakeResponse()) as mocked:
            first = self.api.get("/api/geo/reverse/", {"lat": "41.31001", "lng": "69.27001"})
            second = self.api.get("/api/geo/reverse/", {"lat": "41.31002", "lng": "69.27002"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), {"address_text": "Tashkent, Chilanzar"})
        self.assertEqual(second.json(), {"address_text": "Tashkent, Chilanzar"})
        mocked.assert_called_once()
        request = mocked.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), "MasterGo/1.0")
