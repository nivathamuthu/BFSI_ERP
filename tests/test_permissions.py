from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_desk_permissions(underwriter_client, adjuster_client, customer, active_policy):
    today = timezone.localdate()
    policy = underwriter_client.post(
        "/api/policies/",
        {
            "customer": customer.id,
            "type": "travel",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=30)),
            "premium_amount": "2500.00",
        },
        format="json",
    )
    assert policy.status_code == 201

    adjuster_policy = adjuster_client.post(
        "/api/policies/",
        {
            "customer": customer.id,
            "type": "travel",
            "start_date": str(today),
            "end_date": str(today + timedelta(days=30)),
            "premium_amount": "2500.00",
        },
        format="json",
    )
    assert adjuster_policy.status_code == 403
    assert adjuster_client.get("/api/policies/").status_code == 200

    claim = adjuster_client.post(
        "/api/claims/",
        {
            "policy": active_policy.id,
            "claimant_name": customer.name,
            "claim_date": str(today - timedelta(days=3)),
            "description": "Outpatient visit.",
            "amount": "1500.00",
        },
        format="json",
    )
    assert claim.status_code == 201
    assert underwriter_client.post(
        "/api/claims/",
        {
            "policy": active_policy.id,
            "claimant_name": customer.name,
            "claim_date": str(today - timedelta(days=3)),
            "description": "Underwriter should not open this.",
            "amount": "1500.00",
        },
        format="json",
    ).status_code == 403

    invoice = adjuster_client.post(
        "/api/finance/invoices/",
        {
            "customer": customer.id,
            "amount": "100.00",
            "due_date": str(today),
        },
        format="json",
    )
    assert invoice.status_code == 403
    assert adjuster_client.get("/api/finance/invoices/").status_code == 200

    verify = adjuster_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "passport", "document_number": "P1234567"},
        format="json",
    )
    assert verify.status_code == 403
    assert underwriter_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "passport", "document_number": "P1234567"},
        format="json",
    ).status_code == 201
