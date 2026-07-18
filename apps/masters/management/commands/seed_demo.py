from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.billing.models import MasterWallet
from apps.billing.services import top_up_wallet
from apps.masters.models import MasterCategoryPrice, MasterProfile, MasterStatus, ServiceCategory
from apps.orders.models import MasterOfferStatus, OrderStatus
from apps.orders.services import transition_order


class Command(BaseCommand):
    help = "Seed demo users, approved master, balance, and category prices for the prototype flow."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-active-orders",
            action="store_true",
            help="Release active orders assigned to the demo master so local smoke flows can start cleanly.",
        )

    def handle(self, *args, **options):
        call_command("seed_categories")

        client, _ = User.objects.get_or_create(
            phone="+998901111111",
            defaults={"full_name": "Demo Client", "language": "ru"},
        )
        master_user, _ = User.objects.get_or_create(
            phone="+998902222222",
            defaults={"full_name": "Demo Master", "language": "ru", "is_master_enabled": True},
        )
        master_user.is_master_enabled = True
        master_user.save(update_fields=["is_master_enabled", "updated_at"])

        master, _ = MasterProfile.objects.update_or_create(
            user=master_user,
            defaults={
                "status": MasterStatus.APPROVED,
                "bio": "Demo electrician for prototype flow.",
                "activity_points": 700,
                "rating": Decimal("4.90"),
                "is_online": True,
                "current_latitude": Decimal("41.311081"),
                "current_longitude": Decimal("69.240562"),
            },
        )

        category = ServiceCategory.objects.get(slug="electrician")
        MasterCategoryPrice.objects.update_or_create(
            master=master,
            category=category,
            defaults={"min_price_uzs": 80_000, "max_price_uzs": 250_000, "is_active": True},
        )

        wallet, _ = MasterWallet.objects.get_or_create(master=master)
        if wallet.balance_uzs <= 40_000:
            top_up_wallet(wallet, 50_000, note="Demo top-up")
        if wallet.free_orders_remaining < 10:
            wallet.free_orders_remaining = 10
            wallet.save(update_fields=["free_orders_remaining", "updated_at"])

        if options["reset_active_orders"]:
            reset_count = self._reset_active_orders(master)
            self.stdout.write(f"Reset active demo orders: {reset_count}")

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"Client phone: {client.phone}")
        self.stdout.write(f"Master phone: {master_user.phone}")
        self.stdout.write("Mock OTP code: 0000")

    def _reset_active_orders(self, master: MasterProfile) -> int:
        active_statuses = [
            OrderStatus.OFFERED_TO_MASTER,
            OrderStatus.ACCEPTED_BY_MASTER,
            OrderStatus.PRICE_PROPOSED,
            OrderStatus.PRICE_ACCEPTED,
            OrderStatus.MASTER_ON_WAY,
            OrderStatus.MASTER_ARRIVED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.WORK_DONE,
            OrderStatus.DISPUTED,
        ]
        reset_count = 0
        for order in master.orders.filter(status__in=active_statuses).order_by("created_at"):
            order.master_offers.filter(status=MasterOfferStatus.PENDING).update(status=MasterOfferStatus.EXPIRED)
            if order.status in {
                OrderStatus.OFFERED_TO_MASTER,
                OrderStatus.ACCEPTED_BY_MASTER,
                OrderStatus.PRICE_PROPOSED,
                OrderStatus.PRICE_ACCEPTED,
                OrderStatus.MASTER_ON_WAY,
                OrderStatus.MASTER_ARRIVED,
            }:
                transition_order(order, OrderStatus.CANCELLED, reason="demo_seed_reset")
            elif order.status == OrderStatus.IN_PROGRESS:
                order = transition_order(order, OrderStatus.WORK_DONE, reason="demo_seed_reset")
                transition_order(order, OrderStatus.COMPLETED, reason="demo_seed_reset")
            elif order.status in {OrderStatus.WORK_DONE, OrderStatus.DISPUTED}:
                transition_order(order, OrderStatus.COMPLETED, reason="demo_seed_reset")
            reset_count += 1
        return reset_count
