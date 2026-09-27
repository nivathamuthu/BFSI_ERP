from django.contrib import admin

from finance.models import Invoice, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_number", "type", "amount", "date", "customer")
    list_filter = ("type",)
    search_fields = ("transaction_number", "description", "customer__name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "amount", "due_date", "status")
    list_filter = ("status",)
    search_fields = ("invoice_number", "customer__name")
