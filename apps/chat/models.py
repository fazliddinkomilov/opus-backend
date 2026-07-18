import uuid

from django.conf import settings
from django.db import models


class MessageKind(models.TextChoices):
    TEXT = "text", "Text"
    PHOTO = "photo", "Photo"
    VIDEO = "video", "Video"
    PRICE_PROPOSAL = "price_proposal", "Price proposal"
    SYSTEM = "system", "System"


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="chat_room")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Chat for {self.order_id}"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="chat_messages")
    kind = models.CharField(max_length=32, choices=MessageKind.choices, default=MessageKind.TEXT)
    text = models.TextField(blank=True)
    attachment_url = models.URLField(blank=True)
    price_uzs = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.room_id} / {self.sender} / {self.kind}"

