from django.db.models import Prefetch, Q

from django_filters import rest_framework as django_filters
from organisations.models import Membership, MembershipType, Organisation
from organisations.serializers import OrganisationSerializer
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse

from surveys.models import Survey, SurveyFollowUp
from surveys.permissions import CanCreateSurvey, CanDeleteSurvey
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer, SurveySerializer


class SurveyPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100

    organisations = []

    def paginate_queryset(self, queryset, request, view=None):
        org_ids = queryset.values_list("organisation_id", flat=True).distinct().order_by()
        self.organisations = Organisation.objects.filter(id__in=org_ids)
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return DRFResponse(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
                "organisations": OrganisationSerializer(self.organisations, many=True).data,
            }
        )


class SurveyFilterSet(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="lte")
    organisation = django_filters.NumberFilter(field_name="organisation_id")

    class Meta:
        model = Survey
        fields = []


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
    pagination_class = SurveyPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    ordering_fields = ["creation_date", "id"]
    filterset_class = SurveyFilterSet

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
    Seuls les rôles RESPONDER sont pris en compte — les ADMIN obtiennent une liste vide.
    """

    serializer_class = FullSurveySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        active_follow_ups = Prefetch("follow_ups", queryset=SurveyFollowUp.objects.filter(is_active=True))
        return _responder_survey_queryset(self.request.user).prefetch_related(active_follow_ups)


class SurveyRetrieveUpdateDestroyAPIView(SurveyQuerySetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = FullSurveySerializer

    def get_queryset(self):
        active_follow_ups = Prefetch("follow_ups", queryset=SurveyFollowUp.objects.filter(is_active=True))
        return super().get_queryset().prefetch_related(active_follow_ups)

    def perform_destroy(self, survey):
        from responses.models import Response as ResponseModel

        survey.deactivate()

        # En utilsant "update" pour la désactivation des réponses on rend l'opération plus
        # rapide même si on bypass les triggers (comme par ex. django simple history). C'est
        # un choix qui peut évoluer plus tard
        survey.responses.update(is_active=False)
        ResponseModel.objects.filter(survey_follow_up__parent_survey=survey).update(is_active=False)

    def get_permissions(self):
        if self.request.method == "DELETE" or self.request.method == "PUT" or self.request.method == "PATCH":
            return [IsAuthenticated(), CanDeleteSurvey()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return SurveySerializer
        return FullSurveySerializer
