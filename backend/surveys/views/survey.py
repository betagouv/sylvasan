from django.db.models import Q

from organisations.models import Membership, MembershipType
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import Survey
from surveys.permissions import CanCreateSurvey
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer, SurveySerializer


class SurveyQuerySetMixin:
    def get_queryset(self):
        user = self.request.user

        org_ids = Membership.objects.filter(user=user, pole__isnull=True).values_list("organisation_id", flat=True)
        pole_ids = Membership.objects.filter(user=user, pole__isnull=False).values_list("pole_id", flat=True)

        return Survey.objects.filter(Q(organisation_id__in=org_ids) | Q(pole_id__in=pole_ids))


class SurveyListCreateAPIView(SurveyQuerySetMixin, ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return SurveyDisplaySerializer
        return SurveySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateSurvey()]
        return [IsAuthenticated()]


class SurveyResponderListAPIView(ListAPIView):
    """
    Retourne seulement les enquêtes auxquelles l'utilisateur·ice connecté·e peut répondre.
    Seuls les rôles RESPONDER sont pris en compte — les ADMIN et MANAGER obtiennent une liste vide.
    """

    serializer_class = FullSurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        org_ids = Membership.objects.filter(
            user=user, membership_type=MembershipType.RESPONDER, pole__isnull=True
        ).values_list("organisation_id", flat=True)

        pole_ids = Membership.objects.filter(
            user=user, membership_type=MembershipType.RESPONDER, pole__isnull=False
        ).values_list("pole_id", flat=True)

        return Survey.objects.filter(Q(organisation_id__in=org_ids) | Q(pole_id__in=pole_ids))


class SurveyRetrieveAPIView(SurveyQuerySetMixin, RetrieveAPIView):
    serializer_class = FullSurveySerializer
    permission_classes = [IsAuthenticated]
