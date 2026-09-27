from decimal import Decimal

# Open claims on the same policy are suspicious. Settled and rejected claims are not.
OPEN_CLAIM_STATUSES = ("intake", "under_review", "approved")
FRAUD_AMOUNT_THRESHOLD = Decimal("100000.00")


def evaluate_claim_fraud(claim) -> list[str]:
    """Rules stand-in for a fraud model. Flags are explanations, not an automatic denial."""
    flags = []
    amount = Decimal(str(claim.amount)) if claim.amount not in (None, "") else Decimal("0")
    if amount >= FRAUD_AMOUNT_THRESHOLD:
        flags.append("amount_exceeds_threshold")

    customer_name = claim.policy.customer.name.strip().lower()
    claimant = (claim.claimant_name or "").strip().lower()
    if claimant != customer_name:
        flags.append("claimant_name_mismatch")

    if claim.claim_date < claim.policy.start_date or claim.claim_date > claim.policy.end_date:
        flags.append("claim_outside_policy_period")

    others = claim.policy.claims.filter(status__in=OPEN_CLAIM_STATUSES)
    if claim.pk:
        others = others.exclude(pk=claim.pk)
    if others.exists():
        flags.append("duplicate_open_claim")
    return flags


def apply_fraud_flags(claim) -> list[str]:
    flags = evaluate_claim_fraud(claim)
    claim.fraud_flags = flags
    claim.fraud_flagged = bool(flags)
    return flags
