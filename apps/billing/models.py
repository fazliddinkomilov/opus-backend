from django.db import models

from apps.masters.models import MasterProfile


class LedgerEntryType(models.TextChoices):
    MANUAL_TOP_UP = "manual_top_up", "Manual top-up"
    PACKAGE_PURCHASE = "package_purchase", "Package purchase"
    ORDER_DEBIT = "order_debit", "Order debit"
    ADJUSTMENT = "adjustment", "Adjustment"


class MasterWallet(models.Model):
    master = models.OneToOneField(MasterProfile, on_delete=models.CASCADE, related_name="wallet")
    balance_uzs = models.PositiveIntegerField(default=0)
    package_orders_remaining = models.PositiveIntegerField(default=0)
    free_orders_remaining = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.master}: {self.balance_uzs} UZS"


class MasterLedgerEntry(models.Model):
    wallet = models.ForeignKey(MasterWallet, on_delete=models.CASCADE, related_name="ledger_entries")
    entry_type = models.CharField(max_length=32, choices=LedgerEntryType.choices)
    amount_uzs = models.IntegerField()
    balance_after_uzs = models.IntegerField()
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_ledger_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.wallet} / {self.entry_type} / {self.amount_uzs}"
