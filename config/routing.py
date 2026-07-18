from django.urls import path

from apps.chat.consumers import ChatConsumer
from apps.orders.consumers import MasterOrdersConsumer, OrderConsumer


websocket_urlpatterns = [
    path("ws/orders/<uuid:order_id>/", OrderConsumer.as_asgi()),
    path("ws/masters/orders/", MasterOrdersConsumer.as_asgi()),
    path("ws/chat/<uuid:room_id>/", ChatConsumer.as_asgi()),
]
