from django.urls import include, path
from rest_framework.routers import SimpleRouter

from documents.views import DocumentViewSet

router = SimpleRouter()
router.register("", DocumentViewSet, basename="document")

urlpatterns = [path("", include(router.urls))]
