from decimal import Decimal

from django.db.models import Sum

from finance.models import Invoice, Transaction


def _total(queryset):
    return queryset.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def customer_outstanding(customer) -> dict:
    """Receivable = open invoices - payments + refunds.

    Issued and overdue invoices are open. Paid and void invoices are not.
    Premium, payout, and adjustment transactions are stored but do not change this figure,
    because the invoice already represents the amount billed.
    """
    open_invoices = Invoice.objects.filter(
        customer=customer,
        status__in=(Invoice.Status.ISSUED, Invoice.Status.OVERDUE),
    )
    open_invoice_total = _total(open_invoices)
    payment_total = _total(
        Transaction.objects.filter(customer=customer, type=Transaction.Type.PAYMENT)
    )
    refund_total = _total(
        Transaction.objects.filter(customer=customer, type=Transaction.Type.REFUND)
    )
    return {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "open_invoice_count": open_invoices.count(),
        "open_invoice_total": open_invoice_total,
        "payment_total": payment_total,
        "refund_total": refund_total,
        "outstanding_balance": open_invoice_total - payment_total + refund_total,
    }
