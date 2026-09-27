from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core.constants import ALL_STAFF, UserRole
from core.permissions import RolePermission
from identity.models import IdentityVerificationRequest
from identity.serializers import IdentityVerificationSerializer, IdentityVerifySerializer


@extend_schema(request=IdentityVerifySerializer, responses={201: IdentityVerificationSerializer})
class VerifyIdentityView(APIView):
    """Run the mock KYC check and store the result. This does not call a real provider."""

    permission_classes = [RolePermission]
    read_roles = ALL_STAFF
    write_roles = (UserRole.UNDERWRITER,)

    def post(self, request):
        serializer = IdentityVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            IdentityVerificationSerializer(record, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class IdentityVerificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """History of mock KYC decisions. Creating a decision happens at /api/identity/verify/."""

    queryset = IdentityVerificationRequest.objects.select_related("customer")
    serializer_class = IdentityVerificationSerializer
    permission_classes = [RolePermission]
    read_roles = ALL_STAFF
    write_roles = ()
    filterset_fields = ["status", "customer", "document_type"]
    search_fields = ["document_number", "customer__name"]
    ordering_fields = ["created_at", "status"]
