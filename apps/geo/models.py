from django.db import models


class MasterLocationPing(models.Model):
    master = models.ForeignKey("masters.MasterProfile", on_delete=models.CASCADE, related_name="location_pings")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="master_pings")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy_meters = models.PositiveSmallIntegerField(null=True, blank=True)
    heading_degrees = models.PositiveSmallIntegerField(null=True, blank=True)
    speed_mps = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.master} / {self.latitude},{self.longitude}"


class MapProvider(models.TextChoices):
    OSM = "osm", "OpenStreetMap"
    MOCK = "mock", "Mock"


class GeoProviderEvent(models.Model):
    provider = models.CharField(max_length=32, choices=MapProvider.choices, default=MapProvider.OSM)
    event_type = models.CharField(max_length=80)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider} / {self.event_type}"
