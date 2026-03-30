from django.db.models import Q

from organisations.models import Membership
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import Survey
from surveys.permissions import CanCreateSurvey
from surveys.serializers import SurveySerializer


class SurveyListCreateAPIView(ListCreateAPIView):
    serializer_class = SurveySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateSurvey()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        org_ids = Membership.objects.filter(user=user, pole__isnull=True).values_list("organisation_id", flat=True)

        pole_ids = Membership.objects.filter(user=user, pole__isnull=False).values_list("pole_id", flat=True)

        return Survey.objects.filter(Q(organisation_id__in=org_ids) | Q(pole_id__in=pole_ids))


class SurveyRetrieveAPIView(RetrieveAPIView):
    serializer_class = SurveySerializer
