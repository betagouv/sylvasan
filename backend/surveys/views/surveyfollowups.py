from django.db.models import Q

from organisations.models import Membership, MembershipType
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import SurveyFollowUp
from surveys.permissions import CanCreateSurvey, CanDeleteSurvey
from surveys.serializers.surveyfollowup import SurveyFollowUpSerializer, SurveyFollowUpWriteSerializer


class SurveyFollowUpQuerySetMixin:
    def get_queryset(self):
        user = self.request.user
        survey_pk = self.kwargs["survey_pk"]

        org_ids = Membership.objects.filter(user=user, pole__isnull=True).values_list("organisation_id", flat=True)
        pole_ids = Membership.objects.filter(user=user, pole__isnull=False).values_list("pole_id", flat=True)
        responder_pole_org_ids = Membership.objects.filter(
            user=user, pole__isnull=False, membership_type=MembershipType.RESPONDER
        ).values_list("organisation_id", flat=True)

        return (
            SurveyFollowUp.objects.active()
            .filter(parent_survey_id=survey_pk)
            .filter(
                Q(organisation_id__in=org_ids)
                | Q(pole_id__in=pole_ids)
                | Q(organisation_id__in=responder_pole_org_ids, pole__isnull=True)
            )
            .distinct()
        )


class SurveyFollowUpListCreateAPIView(SurveyFollowUpQuerySetMixin, ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return SurveyFollowUpSerializer
        return SurveyFollowUpWriteSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateSurvey()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            parent_survey_id=self.kwargs["survey_pk"],
        )


class SurveyFollowUpRetrieveUpdateDestroyAPIView(SurveyFollowUpQuerySetMixin, RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return SurveyFollowUpWriteSerializer
        return SurveyFollowUpSerializer

    def get_permissions(self):
        if self.request.method in ("DELETE", "PUT", "PATCH"):
            return [IsAuthenticated(), CanDeleteSurvey()]
        return [IsAuthenticated()]

    def perform_destroy(self, follow_up):
        follow_up.deactivate()
        follow_up.responses.update(is_active=False)
