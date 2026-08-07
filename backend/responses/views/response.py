import csv
import json

from django.db.models import Prefetch, Q
from django.http import HttpResponse

from django_filters import rest_framework as django_filters
from organisations.models import Membership, MembershipType
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from surveys.models import Survey
from surveys.serializers import SurveyDisplaySerializer

from responses.models import Response
from responses.permissions import CanCreateFollowUpResponse, CanCreateResponse, CanDeleteResponse
from responses.serializers import (
    FollowUpResponseSerializer,
    FullResponseSerializer,
    FullResponseSerializerWithFollowUps,
    ResponseDisplaySerializer,
    ResponseExportSerializer,
    ResponseSerializer,
)


class ResponsePagination(LimitOffsetPagination):
    """
    On ajoute dans le payload les enquêtes afin de pouvoir filtrer par enquête.
    """

    default_limit = 20
    max_limit = 100

    surveys = []

    def paginate_queryset(self, queryset, request, view=None):
        survey_ids = queryset.values_list("survey_id", flat=True).distinct().order_by()
        self.surveys = Survey.objects.filter(id__in=survey_ids)
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return DRFResponse(
            {
                "count": self.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
                "surveys": SurveyDisplaySerializer(self.surveys, many=True).data,
            }
        )


class ResponseFilterSet(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="lte")
    survey = django_filters.NumberFilter(field_name="survey_id")
    include_follow_ups = django_filters.BooleanFilter(method="filter_include_follow_ups")

    class Meta:
        model = Response
        fields = []

    def filter_include_follow_ups(self, queryset, name, value):
        if not value:
            return queryset.filter(survey_follow_up__isnull=True)
        return queryset

    def filter_queryset(self, queryset):
        # Quand le paramètre est absent, on exclut les suivis par défaut
        if "include_follow_ups" not in self.data:
            queryset = queryset.filter(survey_follow_up__isnull=True)
        return super().filter_queryset(queryset)


class ResponseQuerySetMixin:
    def get_queryset(self):
        user = self.request.user
        memberships = list(Membership.objects.filter(user=user))

        if not memberships:
            return Response.objects.none()

        query = Q()
        for membership in memberships:
            if membership.membership_type == MembershipType.RESPONDER:
                query |= Q(respondant=user)
            elif membership.pole_id is not None:
                query |= (
                    Q(survey__pole_id=membership.pole_id)
                    | Q(survey_follow_up__pole_id=membership.pole_id)
                    | Q(
                        survey_follow_up__organisation_id=membership.organisation_id,
                        survey_follow_up__pole__isnull=True,
                    )
                )
            else:
                query |= Q(survey__organisation_id=membership.organisation_id) | Q(
                    survey_follow_up__organisation_id=membership.organisation_id
                )

        return (
            Response.objects.active()
            .filter(query)
            .distinct()
            .select_related("survey", "survey__organisation", "survey__pole", "survey_follow_up")
        )


class ResponseListCreateAPIView(ResponseQuerySetMixin, ListCreateAPIView):
    pagination_class = ResponsePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    ordering_fields = ["creation_date", "id"]
    filterset_class = ResponseFilterSet

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ResponseDisplaySerializer
        if self.request.data.get("survey_follow_up"):
            return FollowUpResponseSerializer
        return ResponseSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            if self.request.data.get("survey_follow_up"):
                return [IsAuthenticated(), CanCreateFollowUpResponse()]
            return [IsAuthenticated(), CanCreateResponse()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(respondant=self.request.user)


class ResponseRetrieveDestroyAPIView(ResponseQuerySetMixin, RetrieveDestroyAPIView):
    serializer_class = FullResponseSerializerWithFollowUps

    def perform_destroy(self, response):
        response.deactivate()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "images",
                "follow_up_responses",
                "follow_up_responses__images",
                "follow_up_responses__survey_follow_up",
                "follow_up_responses__respondant",
            )
        )

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), CanDeleteResponse()]
        return [IsAuthenticated()]


class ResponseFullListAPIView(ListAPIView):
    """
    Retourne la liste complète des réponses de l'utilisateur·ice connecté·e.
    Seuls les rôles RESPONDER sont pris en compte — les ADMIN obtiennent une liste vide.
    """

    serializer_class = FullResponseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        has_responder_membership = Membership.objects.filter(
            user=user, membership_type=MembershipType.RESPONDER
        ).exists()
        if not has_responder_membership:
            return Response.objects.none()
        return (
            Response.objects.active()
            .filter(respondant=user)
            .select_related("survey", "survey__organisation", "survey__pole", "survey_follow_up")
            .prefetch_related("images")
        )


class ResponseExportBaseView(ResponseQuerySetMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [
        django_filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    filterset_class = ResponseFilterSet
    serializer_class = ResponseExportSerializer
    pagination_class = None

    ordering_fields = ["creation_date", "id"]

    def get_queryset(self):
        follow_up_qs = (
            Response.objects.active()
            .select_related("survey_follow_up", "respondant")
            .prefetch_related("images")
            .order_by("creation_date")
        )
        return (
            super()
            .get_queryset()
            .select_related("respondant", "survey")
            .prefetch_related(
                "images",
                Prefetch("follow_up_responses", queryset=follow_up_qs),
            )
        )

    def get_filtered_queryset(self):
        queryset = self.get_queryset()
        return self.filter_queryset(queryset)


class ResponseJsonExportView(ResponseExportBaseView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_filtered_queryset()
        serializer = self.get_serializer(queryset, many=True)
        content = json.dumps(serializer.data, ensure_ascii=False, indent=2)
        response = HttpResponse(content, content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="reponses.json"'
        return response


class ResponseCsvExportView(ResponseExportBaseView):
    def get(self, request, *args, **kwargs):
        import io

        queryset = self.get_filtered_queryset()
        serializer = self.get_serializer(queryset, many=True)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Type",
                "ID enquête",
                "Titre de l'enquête",
                "ID externe répondant",
                "Email répondant",
                "Répondant",
                "Statut",
                "Date de création",
                "Données",
            ]
        )
        for item in serializer.data:
            writer.writerow(_csv_row(item, "Principale"))
            for follow_up in item.get("follow_ups", []):
                writer.writerow(_csv_row(follow_up, "↳ Suivi"))

        response = HttpResponse(
            output.getvalue().encode("utf-8-sig"),
            content_type="text/csv; charset=utf-8-sig",
        )
        response["Content-Disposition"] = 'attachment; filename="reponses.csv"'
        return response


def _csv_row(item, type_label):
    survey = item.get("survey") or {}
    respondant = item.get("respondant") or {}
    first = respondant.get("first_name", "")
    last = respondant.get("last_name", "")
    return [
        item["id"],
        type_label,
        survey.get("id", ""),
        survey.get("title", ""),
        respondant.get("external_id") or "",
        respondant.get("email", ""),
        f"{first} {last}".strip(),
        item["status"],
        item["creation_date"],
        json.dumps(item["data"], ensure_ascii=False),
    ]
