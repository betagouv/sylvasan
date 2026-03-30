from organisations.models import Membership, MembershipType
from rest_framework import permissions


class CanCreateSurvey(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour créer des enquêtes"

    # Pour l'instant seulement les ADMIN peuvent créer des enquêtes
    def has_permission(self, request, view):
        organisation_id = request.data.get("organisation")
        pole_id = request.data.get("pole")

        qs = Membership.objects.filter(
            user=request.user,
            organisation_id=organisation_id,
            membership_type=MembershipType.ADMIN,
        )

        # Un·e ADMIN au niveau de l´organisation peut créer des enquêtes pour les poles
        if qs.filter(pole__isnull=True).exists():
            return True

        # S'il s'agit d'un·e ADMIN au niveau d'un pole, il faut que le pole soit le même
        # que celui donc l'ADMIN a accès
        return pole_id and qs.filter(pole_id=pole_id).exists()
