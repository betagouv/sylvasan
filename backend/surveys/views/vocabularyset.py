import csv
import io
from itertools import chain
from typing import ClassVar

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

from django_filters import rest_framework as django_filters
from organisations.models import Organisation
from organisations.models.membership import MembershipType
from organisations.serializers import OrganisationSerializer
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from users.permissions import HasAdminRole

from surveys.models import VocabularyEntry, VocabularySet
from surveys.serializers import VocabularyEntrySerializer, VocabularySetSerializer
from surveys.views.survey import _responder_survey_queryset


def _active_entries_prefetch():
    return Prefetch(
        "entries",
        queryset=VocabularyEntry.objects.filter(is_active=True).order_by("position"),
    )


def _accessible_vocab_queryset(user):
    """
    VocabularySets visibles par l'utilisateur :
    - soit le référentiel appartient directement à une organisation dont l'utilisateur est membre,
    - soit la catégorie du référentiel est accessible à l'une de ses organisations.
    """
    org_ids = user.memberships.values_list("organisation_id", flat=True)
    category_arrays = Organisation.objects.filter(id__in=org_ids).values_list("vocabulary_categories", flat=True)
    accessible_categories = set(chain.from_iterable(cats or [] for cats in category_arrays))
    return (
        VocabularySet.objects.filter(
            Q(organisation_id__in=org_ids) | Q(category__in=accessible_categories),
            is_active=True,
        )
        .distinct()
        .order_by("code")
    )


class VocabularySetPagination(LimitOffsetPagination):
    default_limit = 30
    max_limit = 500

    # TODO: extract this (identical to SurveyPagination in backend/surveys/views/survey.py) into
    # a different util.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organisations: list = []

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
    filterset_class = VocabularySetFilterSet
    search_fields = (
        "code",
        "name",
    )

    def perform_create(self, serializer):
        """
        Vérifie que l'utilisateur est admin de l'organisation cible avant de créer.
        """
        org = serializer.validated_data["organisation"]
        admin_org_ids = self.request.user.memberships.filter(membership_type=MembershipType.ADMIN).values_list(
            "organisation_id", flat=True
        )
        if org.id not in admin_org_ids:
            raise PermissionDenied()
        serializer.save()


class VocabularySetRetrieveView(VocabularySetAdminMixin, RetrieveDestroyAPIView):
    """Vue pour les admins : Détail d'un référentiel avec toutes ses entrées actives."""

    def perform_destroy(self, obj):
        obj.deactivate()


class VocabularyEntryAdminView(RetrieveUpdateDestroyAPIView):
    """Vue pour les admins : Permet de modifier ou supprimer une entrée."""

    permission_classes = (HasAdminRole,)
    serializer_class = VocabularyEntrySerializer

    def get_queryset(self):
        """
        Limite l'accès aux entrées actives du référentiel indiqué dans l'URL,
        à condition que ce référentiel appartienne à une organisation administrée par l'utilisateur.
        """
        admin_org_ids = self.request.user.memberships.filter(membership_type=MembershipType.ADMIN).values_list(
            "organisation_id", flat=True
        )
        return VocabularyEntry.objects.filter(
            vocabulary_set_id=self.kwargs["vocabularyset_pk"],
            vocabulary_set__organisation_id__in=admin_org_ids,
            vocabulary_set__is_active=True,
            is_active=True,
        )

    def perform_destroy(self, instance):
        instance.deactivate()


class VocabularyEntryAdminCreateView(CreateAPIView):
    """Vue pour les admins : Création d'une entrée dans un référentiel."""

    permission_classes = (HasAdminRole,)
    serializer_class = VocabularyEntrySerializer

    def get_queryset(self):
        admin_org_ids = self.request.user.memberships.filter(membership_type=MembershipType.ADMIN).values_list(
            "organisation_id", flat=True
        )
        return VocabularySet.objects.filter(
            id=self.kwargs["vocabularyset_pk"],
            organisation_id__in=admin_org_ids,
            is_active=True,
        )

    def perform_create(self, serializer):
        """
        Vérifie que le référentiel cible appartient à une organisation administrée
        par l'utilisateur, puis crée l'entrée.
        """
        vocabulary_set = get_object_or_404(self.get_queryset(), pk=self.kwargs["vocabularyset_pk"])
        serializer.save(vocabulary_set=vocabulary_set)


class VocabularyEntryBulkImportView(GenericAPIView):
    """Vue pour les admins : Import CSV d'entrées dans un référentiel."""

    permission_classes = (HasAdminRole,)
    serializer_class = VocabularyEntrySerializer

    def _get_vocabulary_set(self):
        admin_org_ids = self.request.user.memberships.filter(membership_type=MembershipType.ADMIN).values_list(
            "organisation_id", flat=True
        )
        return get_object_or_404(
            VocabularySet,
            pk=self.kwargs["vocabularyset_pk"],
            organisation_id__in=admin_org_ids,
            is_active=True,
        )

    def post(self, request, *args, **kwargs):
        vocabulary_set = self._get_vocabulary_set()

        csv_file = request.FILES.get("file")
        if not csv_file:
            return DRFResponse({"detail": "Fichier CSV manquant."}, status=400)

        # djangorestframework-camel-case convertit dryRun -> dry_run
        dry_run = request.data.get("dry_run", True)
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() not in ("false", "0")

        try:
            content = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return DRFResponse({"detail": "Le fichier doit être encodé en UTF-8."}, status=400)

        try:
            reader = csv.reader(io.StringIO(content))
            rows = [row for row in reader if any(cell.strip() for cell in row)]
        except csv.Error:
            return DRFResponse({"detail": "Impossible de lire le fichier CSV."}, status=400)

        if not rows:
            return DRFResponse({"detail": "Le fichier CSV est vide."}, status=400)

        col_counts = {len(row) for row in rows}
        if min(col_counts) < 2:
            return DRFResponse(
                {"detail": "Le fichier CSV doit contenir au moins 2 colonnes (code, libellé)."},
                status=400,
            )
        if max(col_counts) > 3:
            return DRFResponse(
                {"detail": "Le fichier CSV ne doit pas contenir plus de 3 colonnes (code, libellé, position)."},
                status=400,
            )

        parsed = []
        for i, row in enumerate(rows, start=1):
            code = row[0].strip()
            label = row[1].strip()
            position = None
            if len(row) == 3 and row[2].strip():
                try:
                    position = int(row[2].strip())
                except ValueError:
                    return DRFResponse(
                        {"detail": f"La position à la ligne {i} doit être un nombre entier."},
                        status=400,
                    )
            parsed.append({"code": code, "label": label, "position": position})

        if dry_run:
            simulated = [VocabularyEntry(vocabulary_set=vocabulary_set, **e) for e in parsed]
            serializer = self.get_serializer(simulated, many=True)
            return DRFResponse(serializer.data)

        to_save = [VocabularyEntry(vocabulary_set=vocabulary_set, is_active=True, **e) for e in parsed]
        result = VocabularyEntry.objects.bulk_create(
            to_save,
            update_conflicts=True,
            update_fields=["label", "position", "is_active"],
            unique_fields=["vocabulary_set", "code"],
        )

        serializer = self.get_serializer(result, many=True)
        return DRFResponse(serializer.data, status=201)


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
