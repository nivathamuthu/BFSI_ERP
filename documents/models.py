from django.db import models

from core.models import TimeStampedModel


class Document(TimeStampedModel):
    """A file stored for a policy, claim, underwriting file, or KYC pack."""

    class DocType(models.TextChoices):
        POLICY = "policy", "Policy"
        CLAIM = "claim", "Claim"
        UNDERWRITING = "underwriting", "Underwriting"
        IDENTITY = "identity", "Identity"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=DocType.choices)
    size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to="documents/%Y/%m/")
    policy = models.ForeignKey(
        "policies.Policy",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    claim = models.ForeignKey(
        "claims.Claim",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    underwriting_request = models.ForeignKey(
        "underwriting.UnderwritingRequest",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documents",
    )

    def __str__(self):
        return self.name
