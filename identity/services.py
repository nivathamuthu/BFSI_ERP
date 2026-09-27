from identity.models import IdentityVerificationRequest


def verify_identity(document_type: str, document_number: str) -> tuple[str, str]:
    """Stand-in for a vendor such as Onfido or Jumio.

    Nothing is sent off-box. A number ending in X is a forced failure so a demo
    can show both outcomes. Short or non-alphanumeric numbers fail format checks.
    Passports and national IDs with a normal number verify. Other document types
    stop in manual review.
    """
    number = (document_number or "").strip().upper()
    if number.endswith("X"):
        return (
            IdentityVerificationRequest.Status.FAILED,
            "Mock provider rejected the document.",
        )
    if len(number) < 6 or not number.isalnum():
        return (
            IdentityVerificationRequest.Status.FAILED,
            "Document number failed format checks.",
        )
    if document_type in {
        IdentityVerificationRequest.DocumentType.PASSPORT,
        IdentityVerificationRequest.DocumentType.NATIONAL_ID,
    }:
        return (
            IdentityVerificationRequest.Status.VERIFIED,
            "Mock provider accepted the document.",
        )
    return (
        IdentityVerificationRequest.Status.MANUAL_REVIEW,
        "Mock provider requires manual review.",
    )
