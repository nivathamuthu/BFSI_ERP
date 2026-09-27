from django.contrib import admin

from identity.models import IdentityVerificationRequest


@admin.register(IdentityVerificationRequest)
class IdentityVerificationRequestAdmin(admin.ModelAdmin):
    list_display = ("customer", "document_type", "document_number", "status", "provider")
    list_filter = ("status", "document_type", "provider")
    search_fields = ("document_number", "customer__name")
