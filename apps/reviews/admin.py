from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["order", "author", "target", "rating", "is_public", "created_at"]
    list_filter = ["rating", "is_public"]
    search_fields = ["order__id", "author__phone", "target__phone", "text"]
    readonly_fields = ["created_at"]

