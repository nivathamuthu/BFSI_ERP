from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel
from core.utils import generate_reference


class Transaction(TimeStampedModel):
    """Cash or ledger movement. Payments and refunds affect a customer's balance; other types are recorded only."""

    class Type(models.TextChoices):
        PREMIUM = "premium", "Premium"
        PAYMENT = "payment", "Payment"
        REFUND = "refund", "Refund"
        CLAIM_PAYOUT = "claim_payout", "Claim payout"
        ADJUSTMENT = "adjustment", "Adjustment"

    transaction_number = models.CharField(max_length=40, unique=True, blank=True)
    customer = models.ForeignKey(
        "customers.Customer",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    invoice = models.ForeignKey(
        "finance.Invoice",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Transaction amount must be greater than zero."})

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = generate_reference("TXN")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.transaction_number


class Invoice(TimeStampedModel):
    """Amount billed to a customer. Open invoices (issued or overdue) are the receivable."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        OVERDUE = "overdue", "Overdue"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    TRANSITIONS = {
        Status.DRAFT: {Status.ISSUED, Status.VOID},
        Status.ISSUED: {Status.PAID, Status.OVERDUE, Status.VOID},
        Status.OVERDUE: {Status.PAID, Status.VOID},
        Status.PAID: set(),
        Status.VOID: set(),
    }
    INITIAL_STATUS = Status.DRAFT

    invoice_number = models.CharField(max_length=40, unique=True, blank=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="invoices")
    policy = models.ForeignKey(
        "policies.Policy",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Invoice amount must be greater than zero."})

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_reference("INV")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number
