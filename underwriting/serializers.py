from rest_framework import serializers

from core.transitions import validate_status
from underwriting.models import UnderwritingRequest


class UnderwritingRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = UnderwritingRequest
        fields = [
            "id",
            "customer",
            "customer_name",
            "policy_type",
            "details",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "customer_name", "created_at", "updated_at"]

    def validate(self, attrs):
        validate_status(
            attrs=attrs,
            instance=self.instance,
            graph=UnderwritingRequest.TRANSITIONS,
            initial=UnderwritingRequest.INITIAL_STATUS,
            label="underwriting request",
        )
        return attrs
