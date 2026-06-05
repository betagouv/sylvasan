from organisations.models import Membership, MembershipType
from rest_framework import permissions
from surveys.models import Survey


class CanCreateResponse(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour répondre à cette enquête"

    def has_permission(self, request, view):
        survey_id = request.data.get("survey")

        try:
            survey = Survey.objects.get(pk=survey_id)
        except Survey.DoesNotExist:
            return False

        qs = Membership.objects.filter(
            user=request.user,
            organisation=survey.organisation,
            membership_type=MembershipType.RESPONDER,
        )

        # Un·e RESPONDER au niveau de l'organisation peut répondre à toutes les enquêtes de l'organisation
        if qs.filter(pole__isnull=True).exists():
            return True

        # Un·e RESPONDER au niveau d'un pôle peut répondre :
        # - aux enquêtes de son pôle spécifique
        # - aux enquêtes au niveau organisation (sans pôle)
        if survey.pole is None:
            return qs.filter(pole__isnull=False).exists()
        return qs.filter(pole=survey.pole).exists()
