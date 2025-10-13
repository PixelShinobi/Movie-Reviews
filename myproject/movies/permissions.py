from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read permissions (GET, HEAD, OPTIONS) are allowed for anyone
    - Write permissions (POST, PUT, DELETE) are only allowed for staff users
    """

    def has_permission(self, request, view):
        # SAFE_METHODS = GET, HEAD, OPTIONS (read-only methods)
        if request.method in permissions.SAFE_METHODS:
            return True  # Anyone can read

        # For write methods, user must be staff
        return request.user and request.user.is_staff
