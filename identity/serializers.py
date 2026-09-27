from rest_framework import serializers

from customers.models import Customer
from identity.models import IdentityVerificationRequest
from identity.services import verify_identity


class IdentityVerificationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = IdentityVerificationRequest
        fields = [
            "id",
            "customer",
            "customer_name",
            "document_type",
            "document_number",
            "status",
            "provider",
            "result_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_name",
            "status",
            "provider",
            "result_detail",
            "created_at",
            "updated_at",
        ]


class IdentityVerifySerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    document_type = serializers.ChoiceField(choices=IdentityVerificationRequest.DocumentType.choices)
    document_number = serializers.CharField(max_length=64)

    def create(self, validated_data):
        document_number = validated_data["document_number"].strip().upper()
        decision, detail = verify_identity(validated_data["document_type"], document_number)
        return IdentityVerificationRequest.objects.create(
            customer=validated_data["customer"],
            document_type=validated_data["document_type"],
            document_number=document_number,
            status=decision,
            provider="mock",
            result_detail=detail,
        )
