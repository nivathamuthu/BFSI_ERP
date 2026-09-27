from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.constants import PolicyType, UserRole
from core.models import User
from customers.models import Customer
from policies.models import Policy

PASSWORD = "ValidPass123!"


@pytest.fixture
def api_client():
    return APIClient()


def _user(username, role):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=PASSWORD,
        role=role,
    )


@pytest.fixture
def admin_user(db):
    return _user("admin", UserRole.ADMIN)


@pytest.fixture
def underwriter_user(db):
    return _user("underwriter", UserRole.UNDERWRITER)


@pytest.fixture
def adjuster_user(db):
    return _user("adjuster", UserRole.CLAIMS_ADJUSTER)


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def underwriter_client(underwriter_user):
    client = APIClient()
    client.force_authenticate(user=underwriter_user)
    return client


@pytest.fixture
def adjuster_client(adjuster_user):
    client = APIClient()
    client.force_authenticate(user=adjuster_user)
    return client


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name="Asha Rao",
        email="asha@example.com",
        phone="+919876543210",
        address="12 MG Road, Bengaluru",
    )


@pytest.fixture
def active_policy(customer):
    today = timezone.localdate()
    return Policy.objects.create(
        customer=customer,
        type=PolicyType.HEALTH,
        start_date=today - timedelta(days=200),
        end_date=today + timedelta(days=160),
        premium_amount=Decimal("12000.00"),
        status=Policy.Status.ACTIVE,
    )


@pytest.fixture
def media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path
