from django.urls import include, path
from rest_framework.routers import SimpleRouter

from compliance.views import ComplianceReportViewSet, ComplianceRuleViewSet

router = SimpleRouter()
router.register("rules", ComplianceRuleViewSet, basename="compliance-rule")
router.register("reports", ComplianceReportViewSet, basename="compliance-report")

urlpatterns = [path("", include(router.urls))]
