from django.urls import include, path
from rest_framework.routers import SimpleRouter

from underwriting.views import UnderwritingRequestViewSet

router = SimpleRouter()
router.register("", UnderwritingRequestViewSet, basename="underwriting")

urlpatterns = [path("", include(router.urls))]
