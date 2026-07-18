from decimal import Decimal

from django.test import TestCase

from apps.geo.models import GeoProviderEvent, MapProvider
from apps.geo.providers import OsmPrototypeMapProviderClient


class GeoProviderTests(TestCase):
    def test_geo_provider_event_defaults_to_osm(self):
        event = GeoProviderEvent.objects.create(event_type="route_preview")

        self.assertEqual(event.provider, MapProvider.OSM)

    def test_osm_prototype_provider_returns_straight_line_estimate(self):
        provider = OsmPrototypeMapProviderClient()

        estimate = provider.route_estimate(
            Decimal("41.313000"),
            Decimal("69.242000"),
            Decimal("41.312000"),
            Decimal("69.241000"),
        )

        self.assertGreater(estimate.distance_meters, 130)
        self.assertLess(estimate.distance_meters, 150)
        self.assertEqual(estimate.eta_seconds, 60)
