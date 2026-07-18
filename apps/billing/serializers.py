from rest_framework import serializers

from .models import MasterLedgerEntry, MasterWallet


class MasterLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterLedgerEntry
        fields = ["id", "entry_type", "amount_uzs", "balance_after_uzs", "note", "created_at"]


class MasterWalletSerializer(serializers.ModelSerializer):
    ledger_entries = MasterLedgerEntrySerializer(many=True, read_only=True)

    class Meta:
        model = MasterWallet
        fields = [
            "id",
            "master",
            "balance_uzs",
            "package_orders_remaining",
            "free_orders_remaining",
            "ledger_entries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["master", "balance_uzs", "ledger_entries", "created_at", "updated_at"]


class WalletTopUpSerializer(serializers.Serializer):
    amount_uzs = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True)

