from rest_framework.routers import DefaultRouter

from .views import MasterProfileViewSet, ServiceCategoryViewSet


router = DefaultRouter()
router.register("categories", ServiceCategoryViewSet, basename="category")
router.register("masters", MasterProfileViewSet, basename="master")

urlpatterns = router.urls

