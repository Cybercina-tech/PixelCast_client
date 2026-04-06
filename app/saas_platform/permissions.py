from rest_framework import permissions


class IsDeveloper(permissions.BasePermission):
    """Full platform access (Developer / superuser)."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_developer())
