from django.contrib import admin

from compliance.models import ComplianceReport, ComplianceRule


@admin.register(ComplianceRule)
class ComplianceRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ("report_number", "rule", "report_date", "status")
    list_filter = ("status",)
    search_fields = ("report_number", "details", "rule__name")
