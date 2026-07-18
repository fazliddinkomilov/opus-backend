from django.db import transaction

from .models import LedgerEntryType, MasterLedgerEntry, MasterWallet


@transaction.atomic
def top_up_wallet(wallet: MasterWallet, amount_uzs: int, note: str = "", created_by=None) -> MasterWallet:
    if amount_uzs <= 0:
        raise ValueError("Top-up amount must be positive")
    wallet.balance_uzs += amount_uzs
    wallet.save(update_fields=["balance_uzs", "updated_at"])
    MasterLedgerEntry.objects.create(
        wallet=wallet,
        entry_type=LedgerEntryType.MANUAL_TOP_UP,
        amount_uzs=amount_uzs,
        balance_after_uzs=wallet.balance_uzs,
        note=note,
        created_by=created_by,
    )
    return wallet


@transaction.atomic
def consume_order_from_package(wallet: MasterWallet, note: str = "") -> MasterWallet:
    if wallet.free_orders_remaining > 0:
        wallet.free_orders_remaining -= 1
        wallet.save(update_fields=["free_orders_remaining", "updated_at"])
        return wallet
    if wallet.package_orders_remaining > 0:
        wallet.package_orders_remaining -= 1
        wallet.save(update_fields=["package_orders_remaining", "updated_at"])
        MasterLedgerEntry.objects.create(
            wallet=wallet,
            entry_type=LedgerEntryType.ORDER_DEBIT,
            amount_uzs=0,
            balance_after_uzs=wallet.balance_uzs,
            note=note,
        )
    return wallet
