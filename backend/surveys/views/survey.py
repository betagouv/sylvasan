from django.db.models import Q

from organisations.models import Membership, MembershipType
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import Survey
from surveys.permissions import CanCreateSurvey, CanDeleteSurvey
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer, SurveySerializer


class SurveyQuerySetMixin:
    def get_queryset(self):
        user = self.request.user

        org_ids = Membership.objects.filter(user=user, pole__isnull=True).values_list("organisation_id", flat=True)
        pole_ids = Membership.objects.filter(user=user, pole__isnull=False).values_list("pole_id", flat=True)
        # Les RESPONDER rattachés à un pôle voient aussi les enquêtes au niveau organisation
        responder_pole_org_ids = Membership.objects.filter(
            user=user, pole__isnull=False, membership_type=MembershipType.RESPONDER
        ).values_list("organisation_id", flat=True)

        return (
            Survey.objects.active()
            .filter(
                Q(organisation_id__in=org_ids)
                | Q(pole_id__in=pole_ids)
                | Q(organisation_id__in=responder_pole_org_ids, pole__isnull=True)
            )
            .distinct()
        )


class SurveyListCreateAPIView(SurveyQuerySetMixin, ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return SurveyDisplaySerializer
        return SurveySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateSurvey()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


def _responder_survey_queryset(user):
    """Enquêtes auxquelles user peut répondre (rôle RESPONDER uniquement).
    Les RESPONDER rattachés à un pôle voient aussi les enquêtes sans pôle de la même organisation."""
    org_ids = Membership.objects.filter(
        user=user, membership_type=MembershipType.RESPONDER, pole__isnull=True
    ).values_list("organisation_id", flat=True)

    pole_memberships = list(
        Membership.objects.filter(user=user, membership_type=MembershipType.RESPONDER, pole__isnull=False).values(
            "pole_id", "organisation_id"
        )
    )

    pole_ids = [m["pole_id"] for m in pole_memberships]
    pole_org_ids = [m["organisation_id"] for m in pole_memberships]

    return (
        Survey.objects.active()
        .filter(
            Q(organisation_id__in=org_ids)
            | Q(pole_id__in=pole_ids)
            | Q(organisation_id__in=pole_org_ids, pole__isnull=True)
        )
        .distinct()
    )


class SurveyResponderListAPIView(ListAPIView):
    """
    Retourne seulement les enquêtes auxquelles l'utilisateur·ice connecté·e peut répondre.
    Seuls les rôles RESPONDER sont pris en compte — les ADMIN et MANAGER obtiennent une liste vide.
    """

    serializer_class = FullSurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _responder_survey_queryset(self.request.user)


class SurveyRetrieveDeleteAPIView(SurveyQuerySetMixin, RetrieveDestroyAPIView):
    serializer_class = FullSurveySerializer

    def perform_destroy(self, survey):
        survey.deactivate()

        # En utilsant "update" pour la désactivation des réponses on rend l'opération plus
        # rapide même si on bypass les triggers (comme par ex. django simple history). C'est
        # un choix qui peut évoluer plus tard
        survey.responses.update(is_active=False)

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), CanDeleteSurvey()]
        return [IsAuthenticated()]
