from rest_framework import decorators, response, viewsets

from apps.masters.models import MasterProfile
from apps.masters.services import get_or_create_master_profile

from .models import MasterWallet
from .serializers import MasterWalletSerializer, WalletTopUpSerializer
from .services import top_up_wallet


class MasterWalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MasterWalletSerializer

    def get_queryset(self):
        queryset = MasterWallet.objects.select_related("master__user").prefetch_related("ledger_entries")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(master__user=self.request.user)

    @decorators.action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        profile = get_or_create_master_profile(request.user)
        wallet, _ = MasterWallet.objects.get_or_create(master=profile)
        return response.Response({"wallet": self.get_serializer(wallet).data})

    @decorators.action(detail=False, methods=["post"], url_path="top-up")
    def top_up_me(self, request):
        profile = get_or_create_master_profile(request.user)
        wallet, _ = MasterWallet.objects.get_or_create(master=profile)
        serializer = WalletTopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = top_up_wallet(
            wallet,
            serializer.validated_data["amount_uzs"],
            serializer.validated_data.get("note", "Prototype manual top-up"),
            created_by=request.user,
        )
        return response.Response({"wallet": self.get_serializer(wallet).data})
