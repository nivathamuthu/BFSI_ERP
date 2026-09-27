from core.constants import ALL_STAFF
from core.viewsets import StaffModelViewSet
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(StaffModelViewSet):
    """Policyholders and billing contacts shared by every desk."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    write_roles = ALL_STAFF
    filterset_fields = ["email"]
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["created_at", "name", "email"]
