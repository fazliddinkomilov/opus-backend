from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.masters.models import MasterProfile, MasterStatus, ServiceCategory
from apps.orders.models import MasterOffer, MasterOfferStatus, Order, OrderStatus
from apps.orders.services import transition_order


class MasterAnalyticsTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.category = ServiceCategory.objects.create(
            slug="electrician",
            name_ru="Электрик",
            name_uz="Elektrik",
            icon="bolt",
            sort_order=1,
        )
        self.client = User.objects.create_user(phone="+998901111111", full_name="Client")
        self.master_user = User.objects.create_user(phone="+998902222222", full_name="Master")
        self.master = MasterProfile.objects.create(
            user=self.master_user,
            status=MasterStatus.APPROVED,
            rating=Decimal("4.90"),
        )

    def test_master_analytics_uses_real_orders_and_offers(self):
        now = timezone.localtime(timezone.now()).replace(hour=10, minute=0, second=0, microsecond=0)
        today_later = now.replace(hour=12)
        yesterday = now - timedelta(days=1)
        today_completed = self._order(
            status=OrderStatus.COMPLETED,
            scheduled_at=now,
            final_price_uzs=420_000,
            completed_at=now,
            address_text="Tashkent, Today 1",
        )
        today_active = self._order(
            status=OrderStatus.MASTER_ON_WAY,
            scheduled_at=today_later,
            agreed_price_uzs=150_000,
            address_text="Tashkent, Today 2",
        )
        self._order(
            status=OrderStatus.COMPLETED,
            scheduled_at=yesterday,
            agreed_price_uzs=356_000,
            completed_at=yesterday,
            address_text="Tashkent, Yesterday",
        )
        self._order(
            status=OrderStatus.COMPLETED,
            scheduled_at=now - timedelta(days=3),
            final_price_uzs=99_000,
            completed_at=now - timedelta(days=3),
            address_text="Tashkent, Old",
        )
        for index, offer_status in enumerate(
            [
                MasterOfferStatus.ACCEPTED,
                MasterOfferStatus.ACCEPTED,
                MasterOfferStatus.ACCEPTED,
                MasterOfferStatus.DECLINED,
                MasterOfferStatus.EXPIRED,
            ],
        ):
            MasterOffer.objects.create(
                order=today_completed if index % 2 == 0 else today_active,
                master=self.master,
                status=offer_status,
                score=1,
                radius_km=1,
                expires_at=now + timedelta(seconds=30),
                responded_at=now,
            )

        self.api.force_authenticate(user=self.master_user)
        response = self.api.get("/api/masters/me/analytics/")

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["earned_today_uzs"], 420_000)
        self.assertEqual(body["earned_yesterday_uzs"], 356_000)
        self.assertEqual(body["orders_today"], 2)
        self.assertEqual(body["acceptance_rate_percent"], 75)
        self.assertEqual(body["rating_avg"], "4.90")
        self.assertEqual(body["total_orders"], 3)
        self.assertEqual(len(body["schedule_today"]), 2)
        self.assertEqual(
            {item["order_id"] for item in body["schedule_today"]},
            {str(today_completed.id), str(today_active.id)},
        )
        active_item = next(item for item in body["schedule_today"] if item["order_id"] == str(today_active.id))
        self.assertEqual(active_item["category"], "electrician")
        self.assertEqual(active_item["amount_uzs"], 150_000)
        self.assertEqual(active_item["address"], "Tashkent, Today 2")

    def test_master_analytics_requires_master_profile(self):
        self.api.force_authenticate(user=self.client)

        response = self.api.get("/api/masters/me/analytics/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "master_profile_required")

    def test_order_transition_broadcasts_analytics_updated_to_master(self):
        order = self._order(
            status=OrderStatus.WORK_DONE,
            final_price_uzs=120_000,
            address_text="Tashkent, Done",
        )
        channel_layer = get_channel_layer()
        channel_name = async_to_sync(channel_layer.new_channel)()
        async_to_sync(channel_layer.group_add)(f"master_user_{self.master_user.id}", channel_name)

        transition_order(order, OrderStatus.COMPLETED, actor=self.client, reason="client_confirmed")

        event = async_to_sync(channel_layer.receive)(channel_name)
        self.assertEqual(event["payload"]["event"], "analytics_updated")
        self.assertEqual(event["payload"]["order_id"], str(order.id))
        self.assertEqual(event["payload"]["status"], OrderStatus.COMPLETED)

    def _order(
        self,
        *,
        status: str,
        address_text: str,
        scheduled_at=None,
        agreed_price_uzs=None,
        final_price_uzs=None,
        completed_at=None,
    ) -> Order:
        order = Order.objects.create(
            client=self.client,
            master=self.master,
            category=self.category,
            status=status,
            description="Analytics order",
            address_text=address_text,
            latitude=Decimal("41.312000"),
            longitude=Decimal("69.241000"),
            scheduled_at=scheduled_at,
            agreed_price_uzs=agreed_price_uzs,
            final_price_uzs=final_price_uzs,
            completed_at=completed_at,
        )
        return order
