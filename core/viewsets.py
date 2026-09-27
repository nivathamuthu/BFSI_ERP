from rest_framework import viewsets

from core.constants import ALL_STAFF
from core.permissions import RolePermission


class StaffModelViewSet(viewsets.ModelViewSet):
    """Authenticated staff API. Subclasses set write_roles; admin always passes."""

    permission_classes = [RolePermission]
    read_roles = ALL_STAFF
    write_roles = ()
    ordering_fields = ["created_at", "updated_at"]
