from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    UNDERWRITER = "underwriter", "Underwriter"
    CLAIMS_ADJUSTER = "claims_adjuster", "Claims Adjuster"


ALL_STAFF = (UserRole.UNDERWRITER, UserRole.CLAIMS_ADJUSTER)


class PolicyType(models.TextChoices):
    LIFE = "life", "Life"
    HEALTH = "health", "Health"
    MOTOR = "motor", "Motor"
    PROPERTY = "property", "Property"
    TRAVEL = "travel", "Travel"
