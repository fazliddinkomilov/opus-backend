from rest_framework.routers import DefaultRouter

from .views import SupportCaseViewSet


router = DefaultRouter()
router.register("support/cases", SupportCaseViewSet, basename="support-case")

urlpatterns = router.urls

