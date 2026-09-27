import pytest
from rest_framework.test import APIClient

from tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_api_root_and_docs_are_public(api_client):
    root = api_client.get("/api/")
    assert root.status_code == 200
    names = {module["name"] for module in root.data["modules"]}
    assert {"Customers", "Policies", "Claims", "Underwriting", "Finance"} <= names

    schema = api_client.get("/api/schema/")
    assert schema.status_code == 200
    assert b"/api/customers/" in schema.content

    docs = api_client.get("/api/docs/")
    assert docs.status_code == 200
    assert b"swagger" in docs.content.lower()

    home = api_client.get("/")
    assert home.status_code == 200
    assert b"Sign in" in home.content

    assert b"outstanding_balance" in schema.content


def test_anonymous_customers_are_rejected(api_client):
    response = api_client.get("/api/customers/")
    assert response.status_code == 401


def test_first_registration_becomes_admin(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "username": "founder",
            "email": "founder@example.com",
            "password": PASSWORD,
            "role": "underwriter",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["user"]["role"] == "admin"
    assert response.data["access"]
    assert response.data["refresh"]


def test_later_registration_cannot_claim_admin(api_client, admin_user):
    rejected = api_client.post(
        "/api/auth/register/",
        {
            "username": "sneaky",
            "email": "sneaky@example.com",
            "password": PASSWORD,
            "role": "admin",
        },
        format="json",
    )
    assert rejected.status_code == 400

    created = api_client.post(
        "/api/auth/register/",
        {
            "username": "newwriter",
            "email": "newwriter@example.com",
            "password": PASSWORD,
            "role": "underwriter",
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.data["user"]["role"] == "underwriter"


def test_login_refresh_and_me(api_client, admin_user):
    login = api_client.post(
        "/api/auth/login/",
        {"username": "admin", "password": PASSWORD},
        format="json",
    )
    assert login.status_code == 200
    assert login.data["role"] == "admin"

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api_client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.data["username"] == "admin"

    refreshed = api_client.post(
        "/api/auth/refresh/",
        {"refresh": login.data["refresh"]},
        format="json",
    )
    assert refreshed.status_code == 200
    assert refreshed.data["access"]


def test_admin_can_change_a_role(admin_client, adjuster_user):
    response = admin_client.patch(
        f"/api/auth/users/{adjuster_user.id}/",
        {"role": "underwriter"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["role"] == "underwriter"

    adjuster_user.refresh_from_db()
    other = APIClient()
    other.force_authenticate(user=adjuster_user)
    denied = other.get("/api/auth/users/")
    assert denied.status_code == 403
