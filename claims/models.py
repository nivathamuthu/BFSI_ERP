from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel
from core.utils import generate_reference


class Claim(TimeStampedModel):
    """A loss reported against one policy. Status moves forward only."""

    class Status(models.TextChoices):
        INTAKE = "intake", "Intake"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SETTLED = "settled", "Settled"

    # Intake is reviewed, then approved or rejected. Only an approved claim can settle.
    TRANSITIONS = {
        Status.INTAKE: {Status.UNDER_REVIEW, Status.REJECTED},
        Status.UNDER_REVIEW: {Status.APPROVED, Status.REJECTED},
        Status.APPROVED: {Status.SETTLED},
        Status.REJECTED: set(),
        Status.SETTLED: set(),
    }
    INITIAL_STATUS = Status.INTAKE

    claim_number = models.CharField(max_length=40, unique=True, blank=True)
    policy = models.ForeignKey("policies.Policy", on_delete=models.PROTECT, related_name="claims")
    claimant_name = models.CharField(max_length=255)
    claim_date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.INTAKE)
    fraud_flagged = models.BooleanField(default=False)
    fraud_flags = models.JSONField(default=list, blank=True)

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Claim amount must be greater than zero."})

    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.claim_number = generate_reference("CLM")
        if self.policy_id:
            from claims.fraud import apply_fraud_flags

            apply_fraud_flags(self)
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"fraud_flagged", "fraud_flags", "claim_number"}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.claim_number
