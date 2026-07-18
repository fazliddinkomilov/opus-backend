from django.conf import settings
from django.utils import timezone
from rest_framework import decorators, permissions, response, viewsets

from apps.billing.models import MasterWallet
from apps.orders.services import match_open_orders

from .models import MasterProfile, MasterStatus, ServiceCategory
from .serializers import (
    MasterAnalyticsSerializer,
    MasterLocationSerializer,
    MasterProfileSerializer,
    ServiceCategorySerializer,
)
from .services import get_master_analytics, get_or_create_master_profile


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceCategory.objects.filter(is_active=True).order_by("sort_order")
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class MasterProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MasterProfileSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = MasterProfile.objects.select_related("user").prefetch_related("category_prices__category", "wallet")
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        profile = MasterProfile.objects.filter(user=request.user).first()
        if request.method == "GET":
            if profile is None:
                return response.Response({"profile": None})
            return response.Response({"profile": self.get_serializer(profile).data})

        serializer = self.get_serializer(profile, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return response.Response({"profile": self.get_serializer(profile).data})

    @decorators.action(detail=False, methods=["get"], url_path="me/analytics")
    def me_analytics(self, request):
        profile = MasterProfile.objects.filter(user=request.user).first()
        if profile is None:
            return response.Response({"code": "master_profile_required"}, status=403)
        analytics = get_master_analytics(profile)
        return response.Response(MasterAnalyticsSerializer(analytics).data)

    @decorators.action(detail=False, methods=["post"], url_path="go-online")
    def go_online(self, request):
        profile = get_or_create_master_profile(request.user)
        wallet = MasterWallet.objects.filter(master=profile).first()
        if profile.status != MasterStatus.APPROVED:
            return response.Response({"code": "master_not_approved"}, status=400)
        if wallet is None or wallet.balance_uzs <= settings.MASTERGO_MIN_MASTER_BALANCE_UZS:
            return response.Response({"code": "balance_too_low", "min_balance_uzs": settings.MASTERGO_MIN_MASTER_BALANCE_UZS}, status=400)
        profile.is_online = True
        profile.last_seen_at = timezone.now()
        profile.save(update_fields=["is_online", "last_seen_at", "updated_at"])
        match_open_orders()
        return response.Response({"profile": self.get_serializer(profile).data})

    @decorators.action(detail=False, methods=["post"], url_path="go-offline")
    def go_offline(self, request):
        profile = get_or_create_master_profile(request.user)
        profile.is_online = False
        profile.last_seen_at = timezone.now()
        profile.save(update_fields=["is_online", "last_seen_at", "updated_at"])
        return response.Response({"profile": self.get_serializer(profile).data})

    @decorators.action(detail=False, methods=["post"], url_path="location")
    def update_location(self, request):
        profile = get_or_create_master_profile(request.user)
        serializer = MasterLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.current_latitude = serializer.validated_data["latitude"]
        profile.current_longitude = serializer.validated_data["longitude"]
        profile.last_seen_at = timezone.now()
        profile.save(update_fields=["current_latitude", "current_longitude", "last_seen_at", "updated_at"])
        if profile.is_online:
            match_open_orders()
        return response.Response({"profile": self.get_serializer(profile).data})
