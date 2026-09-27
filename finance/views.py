from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import ALL_STAFF
from core.permissions import RolePermission
from core.viewsets import StaffModelViewSet
from customers.models import Customer
from finance.models import Invoice, Transaction
from finance.serializers import InvoiceSerializer, OutstandingBalanceSerializer, TransactionSerializer
from finance.services import customer_outstanding


class TransactionViewSet(StaffModelViewSet):
    """Ledger entries. Only payments and refunds change the outstanding-balance figure."""

    queryset = Transaction.objects.select_related("customer", "invoice")
    serializer_class = TransactionSerializer
    filterset_fields = ["type", "customer", "invoice"]
    search_fields = ["transaction_number", "description", "customer__name"]
    ordering_fields = ["created_at", "date", "amount", "type"]


class InvoiceViewSet(StaffModelViewSet):
    """Premium billing. Draft invoices are not yet receivable; issued and overdue invoices are."""

    queryset = Invoice.objects.select_related("customer", "policy")
    serializer_class = InvoiceSerializer
    filterset_fields = ["status", "customer", "policy"]
    search_fields = ["invoice_number", "customer__name", "customer__email"]
    ordering_fields = ["created_at", "due_date", "amount", "status"]


@extend_schema(responses=OutstandingBalanceSerializer)
class OutstandingBalanceView(APIView):
    """Open invoices, minus payments, plus refunds, for one customer."""

    permission_classes = [RolePermission]
    read_roles = ALL_STAFF
    write_roles = ()

    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        payload = customer_outstanding(customer)
        return Response(OutstandingBalanceSerializer(payload).data)
