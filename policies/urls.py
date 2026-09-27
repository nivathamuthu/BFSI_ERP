from django.urls import include, path
from rest_framework.routers import SimpleRouter

from policies.views import PolicyViewSet

router = SimpleRouter()
router.register("", PolicyViewSet, basename="policy")

urlpatterns = [path("", include(router.urls))]
