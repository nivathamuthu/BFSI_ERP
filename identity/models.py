from django.db import models

from core.models import TimeStampedModel


class IdentityVerificationRequest(TimeStampedModel):
    """Result of a KYC check. `provider` is `mock` because no external vendor is called."""

    class DocumentType(models.TextChoices):
        PASSPORT = "passport", "Passport"
        DRIVERS_LICENSE = "drivers_license", "Driver's license"
        NATIONAL_ID = "national_id", "National ID"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"
        MANUAL_REVIEW = "manual_review", "Manual review"

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="identity_verifications",
    )
    document_type = models.CharField(max_length=32, choices=DocumentType.choices)
    document_number = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=32, default="mock")
    result_detail = models.TextField(blank=True)

    def __str__(self):
        return f"{self.document_type} {self.status} for {self.customer}"
