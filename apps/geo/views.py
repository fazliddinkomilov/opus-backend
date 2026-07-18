from django.utils import timezone
from rest_framework import decorators, response, status, viewsets

from apps.masters.models import MasterProfile

from .models import MasterLocationPing
from .providers import get_map_provider_client
from .serializers import (
    MasterLocationPingSerializer,
    ReverseGeocodeRequestSerializer,
    RouteRequestSerializer,
)
from .services import broadcast_master_location_ping, reverse_geocode, search_address


class MasterLocationPingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MasterLocationPingSerializer

    def get_queryset(self):
        queryset = MasterLocationPing.objects.select_related("master__user", "order")
        if self.request.user.is_staff:
            return queryset
        return (queryset.filter(master__user=self.request.user) | queryset.filter(order__client=self.request.user)).distinct()

    @decorators.action(detail=False, methods=["post"])
    def ping(self, request):
        profile = MasterProfile.objects.filter(user=request.user).first()
        if profile is None:
            return response.Response({"code": "master_profile_not_found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MasterLocationPingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data.get("order")
        if order is not None and order.master_id != profile.id:
            return response.Response(
                {"code": "order_not_assigned_to_master"},
                status=status.HTTP_403_FORBIDDEN,
            )
        ping = MasterLocationPing.objects.create(master=profile, **serializer.validated_data)
        profile.current_latitude = ping.latitude
        profile.current_longitude = ping.longitude
        profile.last_seen_at = timezone.now()
        profile.save(update_fields=["current_latitude", "current_longitude", "last_seen_at", "updated_at"])
        broadcast_master_location_ping(ping)
        return response.Response({"ping": self.get_serializer(ping).data}, status=status.HTTP_201_CREATED)


@decorators.api_view(["GET"])
def route(request):
    serializer = RouteRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    route_geometry = get_map_provider_client().route_geometry(
        data["from_latitude"],
        data["from_longitude"],
        data["to_latitude"],
        data["to_longitude"],
    )
    return response.Response(
        {
            "provider": route_geometry.provider,
            "is_fallback": route_geometry.is_fallback,
            "distance_meters": route_geometry.distance_meters,
            "eta_seconds": route_geometry.eta_seconds,
            "points": [
                {"latitude": str(latitude), "longitude": str(longitude)}
                for latitude, longitude in route_geometry.points
            ],
        }
    )


@decorators.api_view(["GET"])
def reverse(request):
    serializer = ReverseGeocodeRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    return response.Response(
        {
            "address_text": reverse_geocode(data["lat"], data["lng"]),
        }
    )


@decorators.api_view(["GET"])
def search(request):
    query = request.query_params.get("q", "")
    results = search_address(query)
    return response.Response({"results": results})
