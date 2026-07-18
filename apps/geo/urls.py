from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MasterLocationPingViewSet,
    reverse as reverse_view,
    route as route_view,
    search as search_view,
)


router = DefaultRouter()
router.register("geo/master-pings", MasterLocationPingViewSet, basename="master-ping")

urlpatterns = [
    *router.urls,
    path("geo/route/", route_view, name="geo-route"),
    path("geo/reverse/", reverse_view, name="geo-reverse"),
    path("geo/search/", search_view, name="geo-search"),
]
