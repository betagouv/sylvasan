from organisations.models.membership import MembershipType
from rest_framework import permissions


class HasAdminRole(permissions.BasePermission):
    """
    Vérifie si l'utilisateur a un rôle admin dans n'importe quelle
    organisation
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.memberships.filter(membership_type=MembershipType.ADMIN).exists()
        )
