from organisations.models import Membership, MembershipType
from rest_framework import permissions
from surveys.models import Survey, SurveyFollowUp
from surveys.permissions import CanDeleteSurvey


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


class CanCreateFollowUpResponse(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour répondre à ce suivi"

    def has_permission(self, request, view):
        # TODO : Cette fonction est très similaire à CanCreateResponse.has_permission.
        # Refactor

        follow_up_id = request.data.get("survey_follow_up")

        try:
            follow_up = SurveyFollowUp.objects.get(pk=follow_up_id)
        except SurveyFollowUp.DoesNotExist:
            return False

        qs = Membership.objects.filter(
            user=request.user,
            organisation=follow_up.organisation,
            membership_type=MembershipType.RESPONDER,
        )

        if qs.filter(pole__isnull=True).exists():
            return True

        if follow_up.pole is None:
            return qs.filter(pole__isnull=False).exists()
        return qs.filter(pole=follow_up.pole).exists()


class CanDeleteResponse(permissions.BasePermission):
    """
    Seuls les utilisateur·ices avec le rôle ADMIN dans l'organisation de l'enquête
    peuvent la supprimer. Vérifié après récupération de l'objet (has_object_permission).
    """

    message = "Vous n'avez pas l'autorisation pour supprimer cette réponse"

    def has_object_permission(self, request, view, obj):
        source = obj.survey_follow_up if obj.survey_follow_up_id else obj.survey
        return CanDeleteSurvey().has_object_permission(request, view, source)
