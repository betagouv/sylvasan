from organisations.models import ApiKey, Membership, MembershipType
from rest_framework import permissions
from surveys.models import Survey, SurveyFollowUp
from surveys.permissions import CanDeleteSurvey


class IsOrganisationAdmin(permissions.BasePermission):
    """
    Vérifie que l'utilisateur est ADMIN de l'organisation demandée (org_id dans l'URL).
    Aucune restriction de pôle : l'accès est accordé si l'utilisateur est admin
    au niveau de l'organisation, quel que soit le pôle.
    """

    message = "Vous n'avez pas l'autorisation pour accéder aux données de cette organisation"

    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        return Membership.objects.filter(
            user=request.user,
            organisation_id=org_id,
            membership_type=MembershipType.ADMIN,
        ).exists()


class IsOrganisationAdminOrHasApiKey(permissions.BasePermission):
    """
    Accorde l'accès si :
    - l'utilisateur connecté est ADMIN de l'organisation demandée, ou
    - la requête porte une clé API valide associée à cette organisation.
    """

    message = "Vous n'avez pas l'autorisation pour accéder aux données de cette organisation"

    def has_permission(self, request, view):
        org_id = view.kwargs.get("org_id")
        if isinstance(request.auth, ApiKey):
            return str(request.auth.organisation_id) == str(org_id)
        if request.user and request.user.is_authenticated:
            return Membership.objects.filter(
                user=request.user,
                organisation_id=org_id,
                membership_type=MembershipType.ADMIN,
            ).exists()
        return False


def _has_responder_permission(request, organisation, pole):
    """Vérifie qu'un·e utilisateur·ice a le rôle RESPONDER pour une ressource donnée."""
    qs = Membership.objects.filter(
        user=request.user,
        organisation=organisation,
        membership_type=MembershipType.RESPONDER,
    )
    if qs.filter(pole__isnull=True).exists():
        return True
    if pole is None:
        return qs.filter(pole__isnull=False).exists()
    return qs.filter(pole=pole).exists()


class CanCreateResponse(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour répondre à cette enquête"

    def has_permission(self, request, view):
        survey_id = request.data.get("survey")
        try:
            survey = Survey.objects.get(pk=survey_id)
        except (SurveyFollowUp.DoesNotExist, ValueError):
            return False
        return _has_responder_permission(request, survey.organisation, survey.pole)


class CanCreateFollowUpResponse(permissions.BasePermission):
    message = "Vous n'avez pas l'autorisation pour répondre à ce suivi"

    def has_permission(self, request, view):
        follow_up_id = request.data.get("survey_follow_up")
        try:
            follow_up = SurveyFollowUp.objects.active().get(pk=follow_up_id)
        except (SurveyFollowUp.DoesNotExist, ValueError):
            return False
        return _has_responder_permission(request, follow_up.organisation, follow_up.pole)


class CanDeleteResponse(permissions.BasePermission):
    """
    Seuls les utilisateur·ices avec le rôle ADMIN dans l'organisation de l'enquête
    peuvent la supprimer. Vérifié après récupération de l'objet (has_object_permission).
    """

    message = "Vous n'avez pas l'autorisation pour supprimer cette réponse"

    def has_object_permission(self, request, view, obj):
        source = obj.survey_follow_up if obj.survey_follow_up_id else obj.survey
        if source is None:
            return False
        return CanDeleteSurvey().has_object_permission(request, view, source)
