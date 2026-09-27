from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def _policy_payload(customer, **overrides):
    today = timezone.localdate()
    payload = {
        "customer": customer.id,
        "type": "health",
        "start_date": str(today),
        "end_date": str(today + timedelta(days=364)),
        "premium_amount": "15000.00",
    }
    payload.update(overrides)
    return payload


def test_customer_crud_search_and_protected_delete(admin_client, active_policy):
    created = admin_client.post(
        "/api/customers/",
        {
            "name": "Meera Iyer",
            "email": "meera@example.com",
            "phone": "+919812345678",
            "address": "8 Boat Club Road, Pune",
        },
        format="json",
    )
    assert created.status_code == 201
    customer_id = created.data["id"]

    bad_phone = admin_client.post(
        "/api/customers/",
        {"name": "Bad Phone", "email": "bad@example.com", "phone": "call-me"},
        format="json",
    )
    assert bad_phone.status_code == 400

    duplicate = admin_client.post(
        "/api/customers/",
        {"name": "Copy", "email": "meera@example.com"},
        format="json",
    )
    assert duplicate.status_code == 400

    listing = admin_client.get("/api/customers/?search=Meera")
    assert listing.status_code == 200
    assert listing.data["count"] == 1

    updated = admin_client.put(
        f"/api/customers/{customer_id}/",
        {
            "name": "Meera Iyer",
            "email": "meera@example.com",
            "phone": "+919812345678",
            "address": "New address",
        },
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["address"] == "New address"

    blocked = admin_client.delete(f"/api/customers/{active_policy.customer_id}/")
    assert blocked.status_code == 409

    deleted = admin_client.delete(f"/api/customers/{customer_id}/")
    assert deleted.status_code == 204


def test_policy_validation_transitions_and_filter(admin_client, customer):
    today = timezone.localdate()
    bad_dates = admin_client.post(
        "/api/policies/",
        _policy_payload(customer, end_date=str(today)),
        format="json",
    )
    assert bad_dates.status_code == 400
    assert "end_date" in bad_dates.data

    bad_premium = admin_client.post(
        "/api/policies/",
        _policy_payload(customer, premium_amount="0"),
        format="json",
    )
    assert bad_premium.status_code == 400

    created = admin_client.post("/api/policies/", _policy_payload(customer), format="json")
    assert created.status_code == 201
    assert created.data["status"] == "draft"
    assert created.data["policy_number"].startswith("POL-")
    policy_id = created.data["id"]

    skipped = admin_client.patch(f"/api/policies/{policy_id}/", {"status": "active"}, format="json")
    assert skipped.status_code == 400

    assert admin_client.patch(f"/api/policies/{policy_id}/", {"status": "quoted"}, format="json").status_code == 200
    active = admin_client.patch(f"/api/policies/{policy_id}/", {"status": "active"}, format="json")
    assert active.status_code == 200

    filtered = admin_client.get(f"/api/policies/?status=active&customer={customer.id}&ordering=premium_amount")
    assert filtered.data["count"] == 1

    replaced = admin_client.put(
        f"/api/policies/{policy_id}/",
        _policy_payload(customer, premium_amount="16000.00", status="active"),
        format="json",
    )
    assert replaced.status_code == 200
    assert replaced.data["premium_amount"] == "16000.00"


def test_policy_binds_only_an_approved_underwriting_request(admin_client, customer):
    submitted = admin_client.post(
        "/api/underwriting/",
        {
            "customer": customer.id,
            "policy_type": "health",
            "details": "Non-smoker, age 34, no recent hospitalization.",
        },
        format="json",
    )
    assert submitted.status_code == 201
    assert submitted.data["status"] == "submitted"
    request_id = submitted.data["id"]

    too_early = admin_client.post(
        "/api/policies/",
        _policy_payload(customer, underwriting_request=request_id),
        format="json",
    )
    assert too_early.status_code == 400

    jumped = admin_client.patch(f"/api/underwriting/{request_id}/", {"status": "approved"}, format="json")
    assert jumped.status_code == 400

    assert admin_client.patch(
        f"/api/underwriting/{request_id}/",
        {"status": "in_review"},
        format="json",
    ).status_code == 200
    approved = admin_client.patch(f"/api/underwriting/{request_id}/", {"status": "approved"}, format="json")
    assert approved.status_code == 200

    locked = admin_client.patch(f"/api/underwriting/{request_id}/", {"status": "declined"}, format="json")
    assert locked.status_code == 400

    bound = admin_client.post(
        "/api/policies/",
        _policy_payload(customer, underwriting_request=request_id),
        format="json",
    )
    assert bound.status_code == 201
    assert bound.data["underwriting_request"] == request_id
