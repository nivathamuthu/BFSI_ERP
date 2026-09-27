from rest_framework import serializers

from compliance.models import ComplianceReport, ComplianceRule
from core.transitions import validate_status


class ComplianceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRule
        fields = ["id", "name", "description", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        validate_status(
            attrs=attrs,
            instance=self.instance,
            graph=ComplianceRule.TRANSITIONS,
            initial=None,
            label="compliance rule",
        )
        return attrs


class ComplianceReportSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = ComplianceReport
        fields = [
            "id",
            "report_number",
            "rule",
            "rule_name",
            "report_date",
            "status",
            "details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "report_number", "rule_name", "created_at", "updated_at"]

    def validate(self, attrs):
        validate_status(
            attrs=attrs,
            instance=self.instance,
            graph=ComplianceReport.TRANSITIONS,
            initial=ComplianceReport.INITIAL_STATUS,
            label="compliance report",
        )
        return attrs
