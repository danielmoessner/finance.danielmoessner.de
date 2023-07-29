from rest_framework import permissions

from .models import Account, Category, Change, Depot


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Only allow access if the object belongs to the user.
        if obj.__class__ == Account or obj.__class__ == Category:
            return obj.depot.user == request.user
        elif obj.__class__ == Depot:
            return obj.user == request.user
        elif obj.__class__ == Change:
            return obj.account.depot.user == request.user

        # Don't allow access as default.
        return False
