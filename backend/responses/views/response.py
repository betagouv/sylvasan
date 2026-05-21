import csv
import json

from django.db.models import Q
from django.http import HttpResponse

from django_filters import rest_framework as django_filters
from organisations.models import Membership, MembershipType
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from responses.models import Response
from responses.permissions import CanCreateResponse
from responses.serializers import FullResponseSerializer, ResponseDisplaySerializer, ResponseSerializer


class ResponsePagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class ResponseFilterSet(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="creation_date", lookup_expr="lte")

    class Meta:
        model = Response
        fields = []


class ResponseQuerySetMixin:
    def get_queryset(self):
        user = self.request.user
        memberships = Membership.objects.filter(user=user)

        if not memberships.exists():
            return Response.objects.none()

        query = Q()
        for membership in memberships:
            if membership.membership_type == MembershipType.RESPONDER:
                query |= Q(respondant=user)
            elif membership.pole is not None:
                query |= Q(survey__pole=membership.pole)
            else:
                query |= Q(survey__organisation=membership.organisation)

        return Response.objects.filter(query).distinct()


class ResponseListCreateAPIView(ResponseQuerySetMixin, ListCreateAPIView):
    pagination_class = ResponsePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
    ]
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


class ResponseFullListAPIView(ListAPIView):
    """
    Retourne la liste complète des réponses de l'utilisateur·ice connecté·e.
    Seuls les rôles RESPONDER sont pris en compte — les ADMIN et MANAGER obtiennent une liste vide.
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
        return Response.objects.filter(respondant=user)


class ResponseExportBaseView(ResponseQuerySetMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = ResponseFilterSet
    serializer_class = FullResponseSerializer
    pagination_class = None

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
                    item["survey"]["title"],
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
