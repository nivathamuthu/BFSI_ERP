from django.contrib import admin

from documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "size", "policy", "claim", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)
