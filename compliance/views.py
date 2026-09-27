from compliance.models import ComplianceReport, ComplianceRule
from compliance.serializers import ComplianceReportSerializer, ComplianceRuleSerializer
from core.viewsets import StaffModelViewSet


class ComplianceRuleViewSet(StaffModelViewSet):
    """Controls the carrier claims to operate. Writing them is an admin task."""

    queryset = ComplianceRule.objects.all()
    serializer_class = ComplianceRuleSerializer
    filterset_fields = ["status"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "status"]


class ComplianceReportViewSet(StaffModelViewSet):
    """Filings against a rule. A report starts as draft and is then submitted."""

    queryset = ComplianceReport.objects.select_related("rule")
    serializer_class = ComplianceReportSerializer
    filterset_fields = ["status", "rule"]
    search_fields = ["report_number", "details", "rule__name"]
    ordering_fields = ["created_at", "report_date", "status"]
