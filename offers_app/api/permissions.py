from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # For Reviews/Offers the owner is 'user' or 'reviewer'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'reviewer'):
            return obj.reviewer == request.user
        return False


class IsBusinessUser(BasePermission):
    """
    Allows access only to business users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.type == 'business'


class IsCustomer(BasePermission):
    """
    Allows access only to customer users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.type == 'customer'


class IsOrderParticipant(BasePermission):
    """
    Allows access if the user is either the customer or the business partner of the order.
    """
    def has_object_permission(self, request, view, obj):
        return obj.customer_user == request.user or obj.business_user == request.user


class IsOrderBusinessOwner(BasePermission):
    """
    Only the business user receiving the order can update its status.
    """
    def has_object_permission(self, request, view, obj):
        return obj.business_user == request.user