from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from core.views import ApiRootView
from portal.views import PortalView

admin.site.site_header = "BFSI Insurance ERP"
admin.site.site_title = "BFSI ERP"
admin.site.index_title = "Operations"

public = {"authentication_classes": [], "permission_classes": [AllowAny]}

urlpatterns = [
    path("", PortalView.as_view(), name="portal"),
    path("admin/", admin.site.urls),
    path("api/", ApiRootView.as_view(), name="api-root"),
    path("api/schema/", SpectacularAPIView.as_view(**public), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema", **public),
        name="swagger-ui",
    ),
    path("api/auth/", include("core.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/policies/", include("policies.urls")),
    path("api/claims/", include("claims.urls")),
    path("api/underwriting/", include("underwriting.urls")),
    path("api/finance/", include("finance.urls")),
    path("api/compliance/", include("compliance.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/identity/", include("identity.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
