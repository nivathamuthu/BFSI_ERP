from claims.models import Claim
from claims.serializers import ClaimSerializer
from core.constants import UserRole
from core.viewsets import StaffModelViewSet


class ClaimViewSet(StaffModelViewSet):
    """Claims desk. Fraud flags are recalculated on every save from the rules in claims.fraud."""

    queryset = Claim.objects.select_related("policy", "policy__customer")
    serializer_class = ClaimSerializer
    write_roles = (UserRole.CLAIMS_ADJUSTER,)
    filterset_fields = ["status", "policy", "fraud_flagged"]
    search_fields = ["claim_number", "claimant_name", "policy__policy_number"]
    ordering_fields = ["created_at", "claim_date", "amount", "status"]
