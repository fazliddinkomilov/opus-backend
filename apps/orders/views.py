from django.db import transaction
from rest_framework import decorators, response, status, viewsets

from apps.billing.services import consume_order_from_package
from apps.chat.services import get_or_create_order_room
from apps.masters.models import MasterProfile

from .models import MasterOfferStatus, Order, OrderAttachment, OrderCancelReason, OrderStatus, PriceProposalStatus
from .serializers import (
    MatchSerializer,
    MasterOfferSerializer,
    OrderCancelSerializer,
    OrderCompleteSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    PriceProposalCreateSerializer,
    PriceProposalSerializer,
)
from .services import (
    OrderActionError,
    accept_master_offer,
    accept_price,
    decline_master_offer,
    expire_master_offer,
    match_open_orders,
    match_order_with_radius_expansion,
    propose_price,
    reject_price,
    transition_order,
)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def _forbidden(self, code: str):
        return response.Response({"code": code}, status=status.HTTP_403_FORBIDDEN)

    def _require_client(self, request, order: Order):
        if order.client_id == request.user.id:
            return None
        return self._forbidden("client_only_action")

    def _get_master_profile(self, request):
        return MasterProfile.objects.filter(user=request.user).first()

    def _require_assigned_master(self, request, order: Order):
        profile = self._get_master_profile(request)
        if profile is None or order.master_id != profile.id:
            return None, self._forbidden("assigned_master_only_action")
        return profile, None

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("client", "master__user", "category")
            .prefetch_related("attachments", "master_offers", "price_proposals")
        )
        if self.request.user.is_staff:
            return queryset
        return (queryset.filter(client=self.request.user) | queryset.filter(master__user=self.request.user)).distinct()

    def perform_create(self, serializer):
        order = serializer.save(client=self.request.user)
        attachments = self.request.FILES.getlist("attachments[]") or self.request.FILES.getlist("attachments")
        for attachment in attachments:
            OrderAttachment.objects.create(order=order, file=attachment)
        get_or_create_order_room(order)
        match_order_with_radius_expansion(order)

    @decorators.action(detail=True, methods=["post"])
    def match(self, request, pk=None):
        order = self.get_object()
        denied = self._require_client(request, order)
        if denied is not None:
            return denied
        serializer = MatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = match_order_with_radius_expansion(order, serializer.validated_data["radius_km"])
        return response.Response(
            {
                "code": "no_master_found" if result.exhausted else "matched",
                "attempted_radii_km": list(result.attempted_radii_km),
                "offer": MasterOfferSerializer(result.offer).data if result.offer else None,
                "order": OrderSerializer(result.order).data,
            }
        )

    @decorators.action(detail=True, methods=["post"], url_path="master-accept")
    def master_accept(self, request, pk=None):
        order = self.get_object()
        profile = self._get_master_profile(request)
        if profile is None:
            return self._forbidden("master_profile_required")
        offer = order.master_offers.filter(master=profile, status=MasterOfferStatus.PENDING).order_by("-created_at").first()
        if offer is None:
            return response.Response({"code": "offer_not_found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            order = accept_master_offer(offer)
        except OrderActionError as error:
            if error.code == "offer_expired":
                expire_master_offer(offer.id)
            return response.Response({"code": error.code}, status=status.HTTP_400_BAD_REQUEST)
        get_or_create_order_room(order)
        return response.Response({"order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"], url_path="master-decline")
    def master_decline(self, request, pk=None):
        order = self.get_object()
        profile = self._get_master_profile(request)
        if profile is None:
            return self._forbidden("master_profile_required")
        offer = order.master_offers.filter(master=profile, status=MasterOfferStatus.PENDING).order_by("-created_at").first()
        if offer is None:
            return response.Response({"code": "offer_not_found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = decline_master_offer(offer, actor=request.user)
        except OrderActionError as error:
            if error.code == "offer_expired":
                expire_master_offer(offer.id)
            return response.Response({"code": error.code}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(
            {
                "code": "no_master_found" if result.exhausted else "matched",
                "attempted_radii_km": list(result.attempted_radii_km),
                "offer": MasterOfferSerializer(result.offer).data if result.offer else None,
                "order": OrderSerializer(result.order).data,
            }
        )

    @decorators.action(detail=True, methods=["post"], url_path="propose-price")
    def create_price_proposal(self, request, pk=None):
        order = self.get_object()
        profile, denied = self._require_assigned_master(request, order)
        if denied is not None:
            return denied
        serializer = PriceProposalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        proposal = propose_price(order, profile, serializer.validated_data["amount_uzs"])
        return response.Response({"proposal": PriceProposalSerializer(proposal).data, "order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"], url_path="accept-price")
    def accept_latest_price(self, request, pk=None):
        order = self.get_object()
        denied = self._require_client(request, order)
        if denied is not None:
            return denied
        proposal = order.price_proposals.filter(status=PriceProposalStatus.PENDING).order_by("-created_at").first()
        if proposal is None:
            return response.Response({"code": "price_proposal_not_found"}, status=status.HTTP_404_NOT_FOUND)
        order = accept_price(proposal, request.user)
        return response.Response({"order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"], url_path="reject-price")
    def reject_latest_price(self, request, pk=None):
        order = self.get_object()
        denied = self._require_client(request, order)
        if denied is not None:
            return denied
        proposal = order.price_proposals.filter(status=PriceProposalStatus.PENDING).order_by("-created_at").first()
        if proposal is None:
            return response.Response({"code": "price_proposal_not_found"}, status=status.HTTP_404_NOT_FOUND)
        order = reject_price(proposal, request.user)
        match_open_orders()
        return response.Response({"order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        _, denied = self._require_assigned_master(request, order)
        if denied is not None:
            return denied
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = transition_order(
            order,
            serializer.validated_data["status"],
            actor=request.user,
            reason=serializer.validated_data.get("reason", "manual_status_update"),
        )
        return response.Response({"order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request, pk=None):
        order = self.get_object()
        denied = self._require_client(request, order)
        if denied is not None:
            return denied
        serializer = OrderCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if order.status != OrderStatus.WORK_DONE:
            return response.Response({"code": "order_not_ready_for_completion"}, status=status.HTTP_400_BAD_REQUEST)
        order.final_price_uzs = serializer.validated_data["final_price_uzs"]
        order.payment_method = serializer.validated_data["payment_method"]
        order.save(update_fields=["final_price_uzs", "payment_method", "updated_at"])
        if order.status == OrderStatus.WORK_DONE:
            order = transition_order(order, OrderStatus.COMPLETED, actor=request.user, reason="client_confirmed")
        if order.master and hasattr(order.master, "wallet"):
            consume_order_from_package(order.master.wallet, note=f"Order {order.id} completed")
        match_open_orders()
        return response.Response({"order": OrderSerializer(order).data})

    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        denied = self._require_client(request, order)
        if denied is not None:
            return denied
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.cancellation_reason = serializer.validated_data.get("reason") or OrderCancelReason.CLIENT_CANCELLED
        order.cancellation_comment = serializer.validated_data.get("comment", "")
        order.save(update_fields=["cancellation_reason", "cancellation_comment", "updated_at"])
        order = transition_order(
            order,
            OrderStatus.CANCELLED,
            actor=request.user,
            reason=order.cancellation_reason,
            metadata={"comment": order.cancellation_comment} if order.cancellation_comment else {},
        )
        match_open_orders()
        return response.Response({"order": OrderSerializer(order).data})
