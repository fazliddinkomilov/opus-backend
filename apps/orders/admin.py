from django.contrib import admin

from .models import MasterOffer, Order, OrderAttachment, OrderEvent, OrderStatus, PriceProposal
from .services import transition_order


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ["actor", "from_status", "to_status", "reason", "metadata", "created_at"]
    can_delete = False


class MasterOfferInline(admin.TabularInline):
    model = MasterOffer
    extra = 0
    readonly_fields = ["master", "status", "score", "radius_km", "expires_at", "responded_at", "created_at"]
    can_delete = False


class PriceProposalInline(admin.TabularInline):
    model = PriceProposal
    extra = 0
    readonly_fields = ["master", "amount_uzs", "status", "created_at", "responded_at"]
    can_delete = False


class OrderAttachmentInline(admin.TabularInline):
    model = OrderAttachment
    extra = 0
    readonly_fields = ["uploaded_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "category",
        "client",
        "master",
        "status",
        "scheduled_at",
        "budget_ceiling_uzs",
        "agreed_price_uzs",
        "final_price_uzs",
        "payment_method",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "category", "payment_method", "scheduled_at", "created_at", "updated_at", "completed_at"]
    search_fields = ["id", "client__phone", "client__full_name", "master__user__phone", "address_text"]
    readonly_fields = ["id", "created_at", "updated_at", "completed_at"]
    date_hierarchy = "created_at"
    inlines = [OrderAttachmentInline, MasterOfferInline, PriceProposalInline, OrderEventInline]
    actions = ["mark_disputed"]

    @admin.action(description="Mark selected orders as disputed")
    def mark_disputed(self, request, queryset):
        updated = 0
        skipped = 0
        for order in queryset:
            if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.EXPIRED}:
                skipped += 1
                continue
            try:
                transition_order(order, OrderStatus.DISPUTED, actor=request.user, reason="admin_mark_disputed")
            except ValueError:
                skipped += 1
            else:
                updated += 1
        self.message_user(request, f"Marked {updated} order(s) as disputed. Skipped {skipped}.")


@admin.register(MasterOffer)
class MasterOfferAdmin(admin.ModelAdmin):
    list_display = ["order", "master", "status", "score", "radius_km", "expires_at", "created_at"]
    list_filter = ["status", "radius_km", "created_at", "expires_at"]
    search_fields = ["order__id", "master__user__phone", "master__user__full_name"]
    date_hierarchy = "created_at"


@admin.register(PriceProposal)
class PriceProposalAdmin(admin.ModelAdmin):
    list_display = ["order", "master", "amount_uzs", "status", "created_at"]
    list_filter = ["status", "created_at", "responded_at"]
    search_fields = ["order__id", "master__user__phone", "master__user__full_name"]
    date_hierarchy = "created_at"


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ["order", "actor", "from_status", "to_status", "reason", "created_at"]
    list_filter = ["from_status", "to_status", "reason", "created_at"]
    search_fields = ["order__id", "actor__phone", "actor__full_name"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(OrderAttachment)
class OrderAttachmentAdmin(admin.ModelAdmin):
    list_display = ["order", "file", "uploaded_at"]
    search_fields = ["order__id", "file"]
    readonly_fields = ["uploaded_at"]
    date_hierarchy = "uploaded_at"
