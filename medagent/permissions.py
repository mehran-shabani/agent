"""
Custom permission classes for MedAgent.

HasActiveSubscription ensures that the requesting user has an active
subscription in the sub app. If no subscription exists, or it is inactive,
access is denied.
"""

from rest_framework.permissions import BasePermission
from sub.models import Subscription

class HasActiveSubscription(BasePermission):
    """Allow access only to users with an active subscription."""

    message = "You must have an active subscription."

    def has_permission(self, request, view):
        try:
            return request.user.subscription.is_active
        except Subscription.DoesNotExist:
            return False
