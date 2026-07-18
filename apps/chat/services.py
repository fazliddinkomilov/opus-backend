from .models import ChatMessage, ChatRoom, MessageKind


def get_or_create_order_room(order) -> ChatRoom:
    room, _ = ChatRoom.objects.get_or_create(order=order)
    return room


def create_text_message(room: ChatRoom, sender, text: str) -> ChatMessage:
    if not text.strip():
        raise ValueError("Message text is required")
    return ChatMessage.objects.create(room=room, sender=sender, kind=MessageKind.TEXT, text=text.strip())


def create_price_message(room: ChatRoom, sender, price_uzs: int) -> ChatMessage:
    if price_uzs <= 0:
        raise ValueError("Price must be positive")
    return ChatMessage.objects.create(
        room=room,
        sender=sender,
        kind=MessageKind.PRICE_PROPOSAL,
        price_uzs=price_uzs,
    )

