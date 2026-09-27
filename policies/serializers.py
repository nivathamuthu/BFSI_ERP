from decimal import Decimal

from rest_framework import serializers

from core.transitions import validate_status
from policies.models import Policy
from underwriting.models import UnderwritingRequest


class PolicySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    premium_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Policy
        fields = [
            "id",
            "policy_number",
            "customer",
            "customer_name",
            "underwriting_request",
            "type",
            "start_date",
            "end_date",
            "premium_amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "policy_number", "customer_name", "created_at", "updated_at"]

    def validate(self, attrs):
        errors = {}
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end <= start:
            errors["end_date"] = "End date must be after start date."

        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        underwriting = attrs.get(
            "underwriting_request",
            getattr(self.instance, "underwriting_request", None),
        )
        if underwriting is not None:
            if underwriting.status != UnderwritingRequest.Status.APPROVED:
                errors["underwriting_request"] = (
                    "Only an approved underwriting request can be bound to a policy."
                )
            elif customer and underwriting.customer_id != customer.id:
                errors["underwriting_request"] = "Underwriting request belongs to a different customer."

        try:
            validate_status(
                attrs=attrs,
                instance=self.instance,
                graph=Policy.TRANSITIONS,
                initial=Policy.INITIAL_STATUS,
                label="policy",
            )
        except serializers.ValidationError as exc:
            errors.update(exc.detail)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
