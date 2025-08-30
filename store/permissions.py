from rest_framework import permissions

class IsAdminOrNotAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        is_admin = bool(request.user and request.user.is_staff)
        is_not_authenticated = bool(not request.user or not request.user.is_authenticated)
        return bool(is_admin or is_not_authenticated)

class IsAdminOrReadyOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)