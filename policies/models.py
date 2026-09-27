from django.core.exceptions import ValidationError
from django.db import models

from core.constants import PolicyType
from core.models import TimeStampedModel
from core.utils import generate_reference


class Policy(TimeStampedModel):
    """A bound or in-progress contract of cover for one customer."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        QUOTED = "quoted", "Quoted"
        ACTIVE = "active", "Active"
        LAPSED = "lapsed", "Lapsed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    # Quote, then bind. Active cover can lapse, expire, or be cancelled. Terminal states stay put.
    TRANSITIONS = {
        Status.DRAFT: {Status.QUOTED, Status.CANCELLED},
        Status.QUOTED: {Status.ACTIVE, Status.CANCELLED},
        Status.ACTIVE: {Status.LAPSED, Status.CANCELLED, Status.EXPIRED},
        Status.LAPSED: {Status.ACTIVE, Status.CANCELLED, Status.EXPIRED},
        Status.CANCELLED: set(),
        Status.EXPIRED: set(),
    }
    INITIAL_STATUS = Status.DRAFT

    policy_number = models.CharField(max_length=40, unique=True, blank=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="policies")
    underwriting_request = models.ForeignKey(
        "underwriting.UnderwritingRequest",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="policies",
    )
    type = models.CharField(max_length=32, choices=PolicyType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)

    def clean(self):
        errors = {}
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            errors["end_date"] = "End date must be after start date."
        if self.premium_amount is not None and self.premium_amount <= 0:
            errors["premium_amount"] = "Premium amount must be greater than zero."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.policy_number:
            self.policy_number = generate_reference("POL")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.policy_number
