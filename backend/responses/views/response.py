from django.db.models import Q

from django_filters import rest_framework as django_filters
from organisations.models import Membership, MembershipType
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from responses.models import Response
from responses.permissions import CanCreateResponse
from responses.serializers import FullResponseSerializer, ResponseDisplaySerializer, ResponseSerializer


class ResponsePagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class ResponseFilterSet(django_filters.FilterSet):
    created_after = django_filters.DateFilter(field_name="creation_date", lookup_expr="gte")
    created_before = django_filters.DateFilter(field_name="creation_date", lookup_expr="lte")

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
