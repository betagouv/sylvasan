from django.core.exceptions import ObjectDoesNotExist

from organisations.models import Membership, MembershipType, Organisation, Pole
from rest_framework import permissions


class CanCreateSurvey(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour créer des enquêtes"

    # Pour l'instant seulement les ADMIN peuvent créer des enquêtes
    def has_permission(self, request, view):
        organisation_id = request.data.get("organisation")
        pole_id = request.data.get("pole")

        if not organisation_id:
            return False

        if pole_id:
            try:
                pole = Pole.objects.get(pk=pole_id)
                organisation = Organisation.objects.get(pk=organisation_id)
                if pole.organisation != organisation:
                    return False
            except ObjectDoesNotExist as _:
                return False

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


class CanDeleteSurvey(permissions.BasePermission):
    """
    Seuls les utilisateur·ices avec le rôle ADMIN dans l'organisation de l'enquête
    peuvent la supprimer. Vérifié après récupération de l'objet (has_object_permission).
    """

    message = "Vous n'avez pas l'autorisation pour supprimer cette enquête"

    def has_object_permission(self, request, view, obj):
        qs = Membership.objects.filter(
            user=request.user,
            organisation=obj.organisation,
            membership_type=MembershipType.ADMIN,
        )
        # Un·e ADMIN au niveau organisation peut supprimer n'importe quelle enquête de l'org
        if qs.filter(pole__isnull=True).exists():
            return True
        # Un·e ADMIN de pôle ne peut supprimer que les enquêtes rattachées à son pôle
        return obj.pole is not None and qs.filter(pole=obj.pole).exists()
