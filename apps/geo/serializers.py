from rest_framework import serializers

from .models import MasterLocationPing


class MasterLocationPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterLocationPing
        fields = [
            "id",
            "master",
            "order",
            "latitude",
            "longitude",
            "accuracy_meters",
            "heading_degrees",
            "speed_mps",
            "created_at",
        ]
        read_only_fields = ["id", "master", "created_at"]


class RouteRequestSerializer(serializers.Serializer):
    from_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    from_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    to_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    to_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class ReverseGeocodeRequestSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)
