"""
Mixins for Django class-based views (non-DRF).
"""
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    """
    Require request.user to have one of ``allowed_roles`` (User.role string values).
    Raises PermissionDenied (403) otherwise.
    """

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        role = getattr(user, 'role', None)
        allowed = getattr(self, 'allowed_roles', None) or ()
        if role not in allowed:
            raise PermissionDenied('You do not have permission to access this page.')
        return super().dispatch(request, *args, **kwargs)
