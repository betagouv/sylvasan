from django.db.models import Prefetch, Q

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import VocabularyEntry, VocabularySet
from surveys.serializers import VocabularySetSerializer


class VocabularySetListView(ListAPIView):
    serializer_class = VocabularySetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # On prend les organisations correspondantes à l'utilisateur·ice ou les
        # vocabulaires sans organisation (donc partagés, org=null)
        org_ids = user.memberships.values_list("organisation_id", flat=True)
        return VocabularySet.objects.filter(
            Q(organisation__in=org_ids) | Q(organisation__isnull=True)
        ).prefetch_related(
            Prefetch(
                "entries",
                queryset=VocabularyEntry.objects.filter(is_active=True).order_by("position"),
            )
        )
