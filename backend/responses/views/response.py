import csv
import json

from django.db.models import Q
from django.http import HttpResponse

from django_filters import rest_framework as django_filters
from organisations.models import Membership, MembershipType
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from surveys.models import Survey
from surveys.serializers import SurveyDisplaySerializer

from responses.models import Response
from responses.permissions import CanCreateResponse
from responses.serializers import (
    FullResponseSerializer,
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

    class Meta:
        model = Response
        fields = []


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
                query |= Q(survey__pole_id=membership.pole_id)
            else:
                query |= Q(survey__organisation_id=membership.organisation_id)

        return (
            Response.objects.active()
            .filter(query)
            .distinct()
            .select_related("survey", "survey__organisation", "survey__pole")
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
        return ResponseSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateResponse()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(respondant=self.request.user)


class ResponseRetrieveAPIView(ResponseQuerySetMixin, RetrieveAPIView):
    serializer_class = FullResponseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("images")


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
            .select_related("survey", "survey__organisation", "survey__pole")
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
        return super().get_queryset().prefetch_related("images")

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
        writer.writerow(["ID", "Enquête", "Répondant", "Statut", "Date de création", "Données"])
        for item in serializer.data:
            respondant = item.get("respondant") or {}
            first = respondant.get("firstName", "")
            last = respondant.get("lastName", "")
            writer.writerow(
                [
                    item["id"],
                    item["survey"],
                    f"{first} {last}".strip(),
                    item["status"],
                    item["creation_date"],
                    json.dumps(item["data"], ensure_ascii=False),
                ]
            )

        response = HttpResponse(
            output.getvalue().encode("utf-8-sig"),
            content_type="text/csv; charset=utf-8-sig",
        )
        response["Content-Disposition"] = 'attachment; filename="reponses.csv"'
        return response
