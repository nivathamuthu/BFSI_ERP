from django.contrib import admin

from policies.models import Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("policy_number", "customer", "type", "status", "premium_amount", "start_date", "end_date")
    list_filter = ("status", "type")
    search_fields = ("policy_number", "customer__name", "customer__email")
