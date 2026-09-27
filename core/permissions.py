from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.constants import UserRole


class IsAdmin(BasePermission):
    message = "Only an admin can perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_superuser or getattr(user, "role", None) == UserRole.ADMIN)


class RolePermission(BasePermission):
    """Admin can do everything. Other roles are limited by the view's read_roles and write_roles."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, "role", None) == UserRole.ADMIN:
            return True

        attr = "read_roles" if request.method in SAFE_METHODS else "write_roles"
        allowed = getattr(view, attr, ()) or ()
        return getattr(user, "role", None) in allowed
