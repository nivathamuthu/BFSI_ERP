from django.urls import include, path
from rest_framework.routers import SimpleRouter

from claims.views import ClaimViewSet

router = SimpleRouter()
router.register("", ClaimViewSet, basename="claim")

urlpatterns = [path("", include(router.urls))]
