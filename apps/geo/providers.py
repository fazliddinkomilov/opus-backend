import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings


@dataclass(frozen=True)
class RouteEstimate:
    distance_meters: int
    eta_seconds: int


@dataclass(frozen=True)
class RouteGeometry:
    points: tuple[tuple[Decimal, Decimal], ...]
    distance_meters: int
    eta_seconds: int
    provider: str
    is_fallback: bool = False


class MapProviderClient:
    def route_estimate(
        self,
        from_latitude: Decimal,
        from_longitude: Decimal,
        to_latitude: Decimal,
        to_longitude: Decimal,
    ) -> RouteEstimate:
        raise NotImplementedError

    def route_geometry(
        self,
        from_latitude: Decimal,
        from_longitude: Decimal,
        to_latitude: Decimal,
        to_longitude: Decimal,
    ) -> RouteGeometry:
        estimate = self.route_estimate(
            from_latitude,
            from_longitude,
            to_latitude,
            to_longitude,
        )
        return RouteGeometry(
            points=((from_latitude, from_longitude), (to_latitude, to_longitude)),
            distance_meters=estimate.distance_meters,
            eta_seconds=estimate.eta_seconds,
            provider="fallback",
            is_fallback=True,
        )


class MockMapProviderClient(MapProviderClient):
    def route_estimate(
        self,
        from_latitude: Decimal,
        from_longitude: Decimal,
        to_latitude: Decimal,
        to_longitude: Decimal,
    ) -> RouteEstimate:
        return RouteEstimate(distance_meters=1200, eta_seconds=900)


class OsmPrototypeMapProviderClient(MapProviderClient):
    average_speed_kph = 22

    def route_estimate(
        self,
        from_latitude: Decimal,
        from_longitude: Decimal,
        to_latitude: Decimal,
        to_longitude: Decimal,
    ) -> RouteEstimate:
        distance_meters = _haversine_meters(
            float(from_latitude),
            float(from_longitude),
            float(to_latitude),
            float(to_longitude),
        )
        meters_per_second = self.average_speed_kph * 1000 / 3600
        eta_seconds = max(60, math.ceil(distance_meters / meters_per_second))
        return RouteEstimate(
            distance_meters=round(distance_meters),
            eta_seconds=eta_seconds,
        )


class OsrmMapProviderClient(OsmPrototypeMapProviderClient):
    provider_name = "osrm"

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 3.0):
        self.base_url = (base_url or getattr(settings, "OSRM_BASE_URL", "")).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def route_geometry(
        self,
        from_latitude: Decimal,
        from_longitude: Decimal,
        to_latitude: Decimal,
        to_longitude: Decimal,
    ) -> RouteGeometry:
        if not self.base_url:
            return super().route_geometry(from_latitude, from_longitude, to_latitude, to_longitude)

        coords = f"{from_longitude},{from_latitude};{to_longitude},{to_latitude}"
        query = urlencode({"overview": "full", "geometries": "geojson", "steps": "false"})
        url = f"{self.base_url}/route/v1/driving/{coords}?{query}"
        request = Request(url, headers={"User-Agent": "MasterGo prototype route adapter"})

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
            fallback = super().route_geometry(from_latitude, from_longitude, to_latitude, to_longitude)
            return RouteGeometry(
                points=fallback.points,
                distance_meters=fallback.distance_meters,
                eta_seconds=fallback.eta_seconds,
                provider=self.provider_name,
                is_fallback=True,
            )

        routes = payload.get("routes")
        if not routes:
            fallback = super().route_geometry(from_latitude, from_longitude, to_latitude, to_longitude)
            return RouteGeometry(
                points=fallback.points,
                distance_meters=fallback.distance_meters,
                eta_seconds=fallback.eta_seconds,
                provider=self.provider_name,
                is_fallback=True,
            )

        route = routes[0]
        coordinates = route.get("geometry", {}).get("coordinates", [])
        points = tuple(
            (Decimal(str(lat)), Decimal(str(lon)))
            for lon, lat in coordinates
            if lon is not None and lat is not None
        )
        if len(points) < 2:
            fallback = super().route_geometry(from_latitude, from_longitude, to_latitude, to_longitude)
            return RouteGeometry(
                points=fallback.points,
                distance_meters=fallback.distance_meters,
                eta_seconds=fallback.eta_seconds,
                provider=self.provider_name,
                is_fallback=True,
            )

        return RouteGeometry(
            points=points,
            distance_meters=round(float(route.get("distance", 0))),
            eta_seconds=round(float(route.get("duration", 0))),
            provider=self.provider_name,
            is_fallback=False,
        )


def get_map_provider_client() -> MapProviderClient:
    if getattr(settings, "OSRM_ENABLED", False):
        return OsrmMapProviderClient()
    return OsmPrototypeMapProviderClient()


def _haversine_meters(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> float:
    earth_radius_meters = 6_371_000
    d_lat = math.radians(to_latitude - from_latitude)
    d_lon = math.radians(to_longitude - from_longitude)
    from_lat = math.radians(from_latitude)
    to_lat = math.radians(to_latitude)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(from_lat) * math.cos(to_lat) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_meters * c
