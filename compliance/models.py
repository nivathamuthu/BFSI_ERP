from django.db import models

from core.models import TimeStampedModel
from core.utils import generate_reference


class ComplianceRule(TimeStampedModel):
    """A control the carrier says it follows, such as KYC before bind."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    TRANSITIONS = {
        Status.ACTIVE: {Status.INACTIVE},
        Status.INACTIVE: {Status.ACTIVE},
    }

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return self.name


class ComplianceReport(TimeStampedModel):
    """Evidence filed against a rule. Draft reports are not yet submitted."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    TRANSITIONS = {
        Status.DRAFT: {Status.SUBMITTED},
        Status.SUBMITTED: {Status.ACCEPTED, Status.REJECTED},
        Status.ACCEPTED: set(),
        Status.REJECTED: set(),
    }
    INITIAL_STATUS = Status.DRAFT

    report_number = models.CharField(max_length=40, unique=True, blank=True)
    rule = models.ForeignKey(
        ComplianceRule,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    report_date = models.DateField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    details = models.TextField()

    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = generate_reference("RPT")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.report_number
