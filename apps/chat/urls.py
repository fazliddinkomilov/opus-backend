from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet, ChatRoomViewSet


router = DefaultRouter()
router.register("chat/rooms", ChatRoomViewSet, basename="chat-room")
router.register("chat/messages", ChatMessageViewSet, basename="chat-message")

urlpatterns = router.urls

