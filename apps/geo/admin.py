from django.contrib import admin

from .models import GeoProviderEvent, MasterLocationPing


@admin.register(MasterLocationPing)
class MasterLocationPingAdmin(admin.ModelAdmin):
    list_display = [
        "master",
        "order",
        "latitude",
        "longitude",
        "accuracy_meters",
        "heading_degrees",
        "speed_mps",
        "created_at",
    ]
    list_filter = ["created_at", "accuracy_meters"]
    search_fields = ["master__user__phone", "master__user__full_name", "order__id"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(GeoProviderEvent)
class GeoProviderEventAdmin(admin.ModelAdmin):
    list_display = ["provider", "event_type", "created_at"]
    list_filter = ["provider", "event_type", "created_at"]
    search_fields = ["event_type"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
