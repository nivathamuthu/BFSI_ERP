from core.constants import UserRole
from core.viewsets import StaffModelViewSet
from underwriting.models import UnderwritingRequest
from underwriting.serializers import UnderwritingRequestSerializer


class UnderwritingRequestViewSet(StaffModelViewSet):
    """Underwriting desk. Approved requests are what a policy may bind to."""

    queryset = UnderwritingRequest.objects.select_related("customer")
    serializer_class = UnderwritingRequestSerializer
    write_roles = (UserRole.UNDERWRITER,)
    filterset_fields = ["status", "policy_type", "customer"]
    search_fields = ["customer__name", "customer__email", "details"]
    ordering_fields = ["created_at", "status", "policy_type"]
