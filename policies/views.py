from core.constants import UserRole
from core.viewsets import StaffModelViewSet
from policies.models import Policy
from policies.serializers import PolicySerializer


class PolicyViewSet(StaffModelViewSet):
    """Policy administration. New contracts start as draft and must be quoted before they go active."""

    queryset = Policy.objects.select_related("customer", "underwriting_request")
    serializer_class = PolicySerializer
    write_roles = (UserRole.UNDERWRITER,)
    filterset_fields = ["status", "type", "customer"]
    search_fields = ["policy_number", "customer__name", "customer__email"]
    ordering_fields = ["created_at", "start_date", "end_date", "premium_amount", "status"]
