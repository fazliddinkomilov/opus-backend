from django.contrib import admin

from .models import ChatMessage, ChatRoom


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["sender", "kind", "text", "attachment_url", "price_uzs", "created_at", "read_at"]
    can_delete = False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "created_at", "closed_at"]
    search_fields = ["id", "order__id"]
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["room", "sender", "kind", "created_at", "read_at"]
    list_filter = ["kind"]
    search_fields = ["room__id", "sender__phone", "sender__full_name", "text"]
    readonly_fields = ["created_at", "read_at"]

