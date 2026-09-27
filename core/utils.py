import uuid

from django.utils import timezone


def generate_reference(prefix: str) -> str:
    """Human-readable unique number such as POL-20260927-A1B2C3."""
    stamp = timezone.now().strftime("%Y%m%d")
    token = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{stamp}-{token}"
