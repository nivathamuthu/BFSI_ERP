from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_outstanding_balance_nets_open_invoices_payments_and_refunds(admin_client, customer, active_policy):
    today = timezone.localdate()
    invoice = admin_client.post(
        "/api/finance/invoices/",
        {
            "customer": customer.id,
            "policy": active_policy.id,
            "amount": "1000.00",
            "due_date": str(today + timedelta(days=15)),
        },
        format="json",
    )
    assert invoice.status_code == 201
    assert invoice.data["status"] == "draft"
    invoice_id = invoice.data["id"]

    skipped = admin_client.patch(f"/api/finance/invoices/{invoice_id}/", {"status": "paid"}, format="json")
    assert skipped.status_code == 400
    assert admin_client.patch(
        f"/api/finance/invoices/{invoice_id}/",
        {"status": "issued"},
        format="json",
    ).status_code == 200

    ignored = admin_client.post(
        "/api/finance/invoices/",
        {
            "customer": customer.id,
            "amount": "500.00",
            "due_date": str(today + timedelta(days=10)),
        },
        format="json",
    )
    ignored_id = ignored.data["id"]
    assert admin_client.patch(f"/api/finance/invoices/{ignored_id}/", {"status": "void"}, format="json").status_code == 200

    payment = admin_client.post(
        "/api/finance/transactions/",
        {
            "invoice": invoice_id,
            "type": "payment",
            "amount": "400.00",
            "date": str(today),
            "description": "Part payment of the health premium",
        },
        format="json",
    )
    assert payment.status_code == 201
    assert payment.data["customer"] == customer.id
    assert payment.data["transaction_number"].startswith("TXN-")

    refund = admin_client.post(
        "/api/finance/transactions/",
        {
            "customer": customer.id,
            "type": "refund",
            "amount": "50.00",
            "date": str(today),
            "description": "Overpayment returned",
        },
        format="json",
    )
    assert refund.status_code == 201

    balance = admin_client.get(f"/api/finance/customers/{customer.id}/outstanding-balance/")
    assert balance.status_code == 200
    assert balance.data["open_invoice_total"] == "1000.00"
    assert balance.data["payment_total"] == "400.00"
    assert balance.data["refund_total"] == "50.00"
    assert balance.data["outstanding_balance"] == "650.00"
    assert balance.data["open_invoice_count"] == 1

    missing = admin_client.get("/api/finance/customers/999999/outstanding-balance/")
    assert missing.status_code == 404


def test_invoice_policy_must_belong_to_the_customer(admin_client, customer, active_policy):
    other = admin_client.post(
        "/api/customers/",
        {"name": "Other Person", "email": "other@example.com"},
        format="json",
    )
    response = admin_client.post(
        "/api/finance/invoices/",
        {
            "customer": other.data["id"],
            "policy": active_policy.id,
            "amount": "100.00",
            "due_date": str(timezone.localdate()),
        },
        format="json",
    )
    assert response.status_code == 400


def test_compliance_report_workflow(admin_client):
    rule = admin_client.post(
        "/api/compliance/rules/",
        {
            "name": "KYC before bind",
            "description": "Identity must be verified before a policy becomes active.",
        },
        format="json",
    )
    assert rule.status_code == 201
    assert rule.data["status"] == "active"

    report = admin_client.post(
        "/api/compliance/reports/",
        {
            "rule": rule.data["id"],
            "report_date": str(timezone.localdate()),
            "details": "Checked the health book for the quarter.",
        },
        format="json",
    )
    assert report.status_code == 201
    assert report.data["status"] == "draft"
    report_id = report.data["id"]

    assert admin_client.patch(
        f"/api/compliance/reports/{report_id}/",
        {"status": "accepted"},
        format="json",
    ).status_code == 400
    assert admin_client.patch(
        f"/api/compliance/reports/{report_id}/",
        {"status": "submitted"},
        format="json",
    ).status_code == 200
    accepted = admin_client.patch(
        f"/api/compliance/reports/{report_id}/",
        {"status": "accepted"},
        format="json",
    )
    assert accepted.status_code == 200
    assert accepted.data["report_number"].startswith("RPT-")
