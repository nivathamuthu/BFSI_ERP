from django.contrib import admin

from claims.models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_number", "policy", "claimant_name", "amount", "status", "fraud_flagged")
    list_filter = ("status", "fraud_flagged")
    search_fields = ("claim_number", "claimant_name", "policy__policy_number")
