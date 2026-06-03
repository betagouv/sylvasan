from django.db.models import Prefetch, Q

from organisations.models import Membership, MembershipType
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import Survey, VocabularyEntry, VocabularySet
from surveys.serializers import VocabularySetDisplaySerializer, VocabularySetSerializer


def _active_entries_prefetch():
    return Prefetch(
        "entries",
        queryset=VocabularyEntry.objects.filter(is_active=True).order_by("position"),
    )


def _accessible_vocab_queryset(user):
    """VocabularySets visibles par l'utilisateur (son organisation ou partagés)."""
    org_ids = user.memberships.values_list("organisation_id", flat=True)
    return VocabularySet.objects.filter(Q(organisation__in=org_ids) | Q(organisation__isnull=True)).order_by("code")


class VocabularySetListView(ListAPIView):
    """Liste des référentiels accessibles — code et nom uniquement, sans les entrées."""

    serializer_class = VocabularySetDisplaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _accessible_vocab_queryset(self.request.user)


class VocabularySetDetailView(RetrieveAPIView):
    """Détail d'un référentiel avec toutes ses entrées actives."""

    serializer_class = VocabularySetSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "code"

    def get_queryset(self):
        return _accessible_vocab_queryset(self.request.user).prefetch_related(_active_entries_prefetch())


class MobileVocabularySetListView(ListAPIView):
    """
    Référentiels complets (avec entrées) restreints aux vocabulaires
    référencés dans les enquêtes auxquelles l'utilisateur·ice peut répondre.
    """

    serializer_class = VocabularySetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        org_ids = Membership.objects.filter(
            user=user, membership_type=MembershipType.RESPONDER, pole__isnull=True
        ).values_list("organisation_id", flat=True)
        pole_ids = Membership.objects.filter(
            user=user, membership_type=MembershipType.RESPONDER, pole__isnull=False
        ).values_list("pole_id", flat=True)

        surveys = Survey.objects.filter(Q(organisation_id__in=org_ids) | Q(pole_id__in=pole_ids)).only("json_schema")

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
