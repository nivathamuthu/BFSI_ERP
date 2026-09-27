from django.db import models

from core.models import TimeStampedModel


class Customer(TimeStampedModel):
    """A person or organization the carrier can underwrite, bill, and pay."""

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name
