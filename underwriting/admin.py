from django.contrib import admin

from underwriting.models import UnderwritingRequest


@admin.register(UnderwritingRequest)
class UnderwritingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "policy_type", "status", "created_at")
    list_filter = ("status", "policy_type")
    search_fields = ("customer__name", "customer__email", "details")
