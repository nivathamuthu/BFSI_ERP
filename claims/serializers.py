from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from claims.models import Claim
from core.transitions import validate_status
from policies.models import Policy


class ClaimSerializer(serializers.ModelSerializer):
    policy_number = serializers.CharField(source="policy.policy_number", read_only=True)
    customer_name = serializers.CharField(source="policy.customer.name", read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Claim
        fields = [
            "id",
            "claim_number",
            "policy",
            "policy_number",
            "customer_name",
            "claimant_name",
            "claim_date",
            "description",
            "amount",
            "status",
            "fraud_flagged",
            "fraud_flags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "claim_number",
            "policy_number",
            "customer_name",
            "fraud_flagged",
            "fraud_flags",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        errors = {}
        claim_date = attrs.get("claim_date", getattr(self.instance, "claim_date", None))
        if claim_date and claim_date > timezone.localdate():
            errors["claim_date"] = "Claim date cannot be in the future."

        policy = attrs.get("policy", getattr(self.instance, "policy", None))
        policy_changed = self.instance is None or (
            "policy" in attrs and policy is not None and policy.pk != self.instance.policy_id
        )
        if policy_changed and policy is not None and policy.status != Policy.Status.ACTIVE:
            errors["policy"] = "Claims can only be opened against an active policy."

        try:
            validate_status(
                attrs=attrs,
                instance=self.instance,
                graph=Claim.TRANSITIONS,
                initial=Claim.INITIAL_STATUS,
                label="claim",
            )
        except serializers.ValidationError as exc:
            errors.update(exc.detail)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
