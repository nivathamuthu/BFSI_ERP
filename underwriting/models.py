from django.db import models

from core.constants import PolicyType
from core.models import TimeStampedModel


class UnderwritingRequest(TimeStampedModel):
    """A risk decision. A policy can be bound to this request only after approval."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        IN_REVIEW = "in_review", "In review"
        REFERRED = "referred", "Referred"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"

    TRANSITIONS = {
        Status.SUBMITTED: {Status.IN_REVIEW, Status.DECLINED},
        Status.IN_REVIEW: {Status.APPROVED, Status.DECLINED, Status.REFERRED},
        Status.REFERRED: {Status.IN_REVIEW, Status.APPROVED, Status.DECLINED},
        Status.APPROVED: set(),
        Status.DECLINED: set(),
    }
    INITIAL_STATUS = Status.SUBMITTED

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="underwriting_requests",
    )
    policy_type = models.CharField(max_length=32, choices=PolicyType.choices)
    details = models.TextField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SUBMITTED)

    def __str__(self):
        return f"{self.policy_type} underwriting for {self.customer}"
