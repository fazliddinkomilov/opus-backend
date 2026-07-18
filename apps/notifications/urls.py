from rest_framework.routers import DefaultRouter

from .views import NotificationEventViewSet


router = DefaultRouter()
router.register("notifications", NotificationEventViewSet, basename="notification")

urlpatterns = router.urls

