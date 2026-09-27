from datetime import timedelta

import pytest
from django.utils import timezone

from core.constants import PolicyType
from policies.models import Policy

pytestmark = pytest.mark.django_db


def _claim_payload(policy, **overrides):
    payload = {
        "policy": policy.id,
        "claimant_name": policy.customer.name,
        "claim_date": str(timezone.localdate() - timedelta(days=10)),
        "description": "Hospital admission for a covered procedure.",
        "amount": "8000.00",
    }
    payload.update(overrides)
    return payload


def test_claim_cannot_skip_or_reverse_status(adjuster_client, active_policy):
    created = adjuster_client.post("/api/claims/", _claim_payload(active_policy), format="json")
    assert created.status_code == 201
    assert created.data["status"] == "intake"
    assert created.data["fraud_flagged"] is False
    assert created.data["claim_number"].startswith("CLM-")
    claim_id = created.data["id"]

    skipped = adjuster_client.patch(f"/api/claims/{claim_id}/", {"status": "settled"}, format="json")
    assert skipped.status_code == 400

    assert adjuster_client.patch(
        f"/api/claims/{claim_id}/",
        {"status": "under_review"},
        format="json",
    ).status_code == 200
    assert adjuster_client.patch(
        f"/api/claims/{claim_id}/",
        {"status": "approved"},
        format="json",
    ).status_code == 200
    settled = adjuster_client.patch(f"/api/claims/{claim_id}/", {"status": "settled"}, format="json")
    assert settled.status_code == 200

    reversed_status = adjuster_client.patch(f"/api/claims/{claim_id}/", {"status": "intake"}, format="json")
    assert reversed_status.status_code == 400


def test_fraud_rules_flag_amount_name_and_period(adjuster_client, active_policy):
    response = adjuster_client.post(
        "/api/claims/",
        _claim_payload(
            active_policy,
            claimant_name="Ravi Rao",
            claim_date=str(active_policy.start_date - timedelta(days=5)),
            amount="250000.00",
        ),
        format="json",
    )
    assert response.status_code == 201
    flags = set(response.data["fraud_flags"])
    assert flags >= {"amount_exceeds_threshold", "claimant_name_mismatch", "claim_outside_policy_period"}
    assert response.data["fraud_flagged"] is True

    flagged = adjuster_client.get("/api/claims/?fraud_flagged=true")
    assert flagged.data["count"] == 1


def test_second_open_claim_is_flagged_as_duplicate(adjuster_client, active_policy):
    first = adjuster_client.post("/api/claims/", _claim_payload(active_policy), format="json")
    second = adjuster_client.post(
        "/api/claims/",
        _claim_payload(active_policy, description="Follow-up visit on the same policy."),
        format="json",
    )
    assert first.status_code == 201
    assert "duplicate_open_claim" not in first.data["fraud_flags"]
    assert second.status_code == 201
    assert "duplicate_open_claim" in second.data["fraud_flags"]


def test_claim_requires_an_active_policy_and_a_past_date(adjuster_client, customer, active_policy):
    today = timezone.localdate()
    draft = Policy.objects.create(
        customer=customer,
        type=PolicyType.HEALTH,
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=300),
        premium_amount="5000.00",
        status=Policy.Status.DRAFT,
    )
    inactive = adjuster_client.post("/api/claims/", _claim_payload(draft), format="json")
    assert inactive.status_code == 400
    assert "policy" in inactive.data

    future = adjuster_client.post(
        "/api/claims/",
        _claim_payload(active_policy, claim_date=str(today + timedelta(days=2))),
        format="json",
    )
    assert future.status_code == 400
    assert "claim_date" in future.data
