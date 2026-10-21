from itertools import chain
from typing import ClassVar

from django.db.models import Prefetch

from django_filters import rest_framework as django_filters
from organisations.models import Organisation
from organisations.models.membership import MembershipType
from organisations.serializers import OrganisationSerializer
from rest_framework import filters
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView, RetrieveDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from users.permissions import HasAdminRole

from surveys.models import VocabularyEntry, VocabularySet
from surveys.serializers import VocabularySetSerializer
from surveys.views.survey import _responder_survey_queryset


def _active_entries_prefetch():
    return Prefetch(
        "entries",
        queryset=VocabularyEntry.objects.filter(is_active=True).order_by("position"),
    )


def _accessible_vocab_queryset(user):
    """VocabularySets visibles par l'utilisateur selon les catégories de ses organisations."""
    org_ids = user.memberships.values_list("organisation_id", flat=True)
    category_arrays = Organisation.objects.filter(id__in=org_ids).values_list("vocabulary_categories", flat=True)
    accessible = set(chain.from_iterable(cats or [] for cats in category_arrays))
    return VocabularySet.objects.filter(
        category__in=accessible,
        is_active=True,
    ).order_by("code")


class VocabularySetPagination(LimitOffsetPagination):
    default_limit = 30
    max_limit = 500

    # TODO: extract this (identical to SurveyPagination in backend/surveys/views/survey.py) into
    # a different util.
    organisations: ClassVar[list] = []

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


class VocabularySetAdminMixin:
    serializer_class = VocabularySetSerializer
    permission_classes = (HasAdminRole,)

    def get_queryset(self):
        """
        Cible les référentiels des organisations pour lequelles l'utilisateur a un
        rôle admin.
        """

        admin_org_ids = self.request.user.memberships.filter(membership_type=MembershipType.ADMIN).values_list(
            "organisation_id", flat=True
        )
        return (
            VocabularySet.objects.filter(organisation_id__in=admin_org_ids, is_active=True)
            .prefetch_related(_active_entries_prefetch())
            .order_by("code")
        )


class VocabularySetFilterSet(django_filters.FilterSet):
    organisation = django_filters.NumberFilter(field_name="organisation_id")

    class Meta:
        model = VocabularySet
        fields: ClassVar[list] = []


class VocabularySetListView(VocabularySetAdminMixin, ListCreateAPIView):
    """Vue utilisée par les admins pour la gestion de référentiels"""

    pagination_class = VocabularySetPagination
    filter_backends: ClassVar[list] = [
        django_filters.DjangoFilterBackend,
        OrderingFilter,
        filters.UnaccentedSearchFilter,
    ]
    search_fields = (
        "code",
        "name",
    )


class VocabularySetRetrieveView(VocabularySetAdminMixin, RetrieveDestroyAPIView):
    """Vue pour les admins : Détail d'un référentiel avec toutes ses entrées actives."""

    def perform_destroy(self, obj):
        obj.deactivate()


class VocabularySetDetailView(RetrieveAPIView):
    """Détail d'un référentiel avec toutes ses entrées actives."""

    serializer_class = VocabularySetSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "code"

    def get_queryset(self):
        return _accessible_vocab_queryset(self.request.user).prefetch_related(_active_entries_prefetch())


class MobileVocabularySetListView(ListAPIView):
    """
    Référentiels complets (avec entrées) restreints aux vocabulaires
    référencés dans les enquêtes auxquelles l'utilisateur·ice peut répondre.
    """

    serializer_class = VocabularySetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        surveys = _responder_survey_queryset(user).only("json_schema")

        vocabulary_codes = set()
        for survey in surveys:
            schema = survey.json_schema or {}
            for field in schema.get("fields", []):
                if field.get("vocabulary"):
                    vocabulary_codes.add(field["vocabulary"])
                for sub_field in field.get("fields", []):
                    if sub_field.get("vocabulary"):
                        vocabulary_codes.add(sub_field["vocabulary"])

        return (
            _accessible_vocab_queryset(user)
            .filter(code__in=vocabulary_codes)
            .prefetch_related(_active_entries_prefetch())
        )
