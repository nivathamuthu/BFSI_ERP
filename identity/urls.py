from django.urls import include, path
from rest_framework.routers import SimpleRouter

from identity.views import IdentityVerificationViewSet, VerifyIdentityView

router = SimpleRouter()
router.register("verifications", IdentityVerificationViewSet, basename="identity-verification")

urlpatterns = [
    path("verify/", VerifyIdentityView.as_view(), name="identity-verify"),
    path("", include(router.urls)),
]
