from rest_framework.routers import DefaultRouter

from .views import MasterWalletViewSet


router = DefaultRouter()
router.register("wallets", MasterWalletViewSet, basename="wallet")

urlpatterns = router.urls

