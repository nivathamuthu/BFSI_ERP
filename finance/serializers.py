from decimal import Decimal

from rest_framework import serializers

from core.transitions import validate_status
from finance.models import Invoice, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_number",
            "customer",
            "customer_name",
            "invoice",
            "type",
            "amount",
            "date",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "transaction_number", "customer_name", "created_at", "updated_at"]

    def validate(self, attrs):
        invoice = attrs.get("invoice", getattr(self.instance, "invoice", None))
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        if invoice is not None and customer is None:
            customer = invoice.customer
            attrs["customer"] = customer
        if invoice is not None and customer is not None and invoice.customer_id != customer.id:
            raise serializers.ValidationError({"invoice": "Invoice does not belong to this customer."})

        txn_type = attrs.get("type", getattr(self.instance, "type", None))
        if txn_type in (Transaction.Type.PAYMENT, Transaction.Type.REFUND) and customer is None:
            raise serializers.ValidationError(
                {"customer": "Payment and refund transactions must be linked to a customer."}
            )
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer",
            "customer_name",
            "policy",
            "amount",
            "due_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "invoice_number", "customer_name", "created_at", "updated_at"]

    def validate(self, attrs):
        errors = {}
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        policy = attrs.get("policy", getattr(self.instance, "policy", None))
        if policy is not None and customer is not None and policy.customer_id != customer.id:
            errors["policy"] = "Policy does not belong to this customer."
        try:
            validate_status(
                attrs=attrs,
                instance=self.instance,
                graph=Invoice.TRANSITIONS,
                initial=Invoice.INITIAL_STATUS,
                label="invoice",
            )
        except serializers.ValidationError as exc:
            errors.update(exc.detail)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class OutstandingBalanceSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    customer_name = serializers.CharField()
    open_invoice_count = serializers.IntegerField()
    open_invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    refund_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
