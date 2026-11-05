from typing import ClassVar

from django.db.models import Prefetch, Q

from organisations.models import Membership
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView
from surveys.models import Placette, PlacetteSurvey

from responses.models import Response
from responses.serializers.geo_combined import PlacetteGeoSerializer
from responses.serializers.response_geo import GeoResponseSerializer
from responses.utils import parse_date, parse_ids, validate_bbox
from responses.views.response_geo import GEO_RESPONSE_LIMIT

GEO_PLACETTE_LIMIT = 500


class CombinedGeoAPIView(APIView):
    """
    Retourne les réponses géolocalisées et les placettes dans la zone de la carte.

    Paramètres obligatoires (degrés décimaux WGS-84) :
        south, west, north, east

    Paramètres optionnels :
        surveys           — identifiants d'enquêtes séparés par des virgules
        placette_surveys  — identifiants de protocoles placettes séparés par des virgules
        after            — date de création minimale, incluse (format YYYY-MM-DD, s'applique aux réponses)
        before           — date de création maximale, incluse (format YYYY-MM-DD, s'applique aux réponses)
        only_mine        — "true" pour ne voir que ses propres réponses
    """

    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        south, west, north, east = validate_bbox(params)

        memberships = list(Membership.objects.filter(user=request.user))

        responses = self._get_responses(request.user, memberships, params, south, west, north, east)
        placettes = self._get_placettes(memberships, params, south, west, north, east)

        return DRFResponse(
            {
                "responses": GeoResponseSerializer(responses, many=True).data,
                "placettes": PlacetteGeoSerializer(placettes, many=True).data,
            }
        )

    def _get_responses(self, user, memberships, params, south, west, north, east):
        from django.contrib.gis.geos import Polygon

        if not memberships:
            return Response.objects.none()

        bbox = Polygon.from_bbox((west, south, east, north))
        bbox.srid = 4326

        query = Q()
        for m in memberships:
            if m.pole_id is None:
                query |= Q(survey__organisation_id=m.organisation_id)
            else:
                query |= Q(survey__pole_id=m.pole_id) | Q(
                    survey__organisation_id=m.organisation_id,
                    survey__pole__isnull=True,
                )

        follow_up_qs = (
            Response.objects.active().select_related("survey_follow_up", "respondant").order_by("-creation_date")
        )

        qs = (
            Response.objects.active()
            .filter(query)
            .filter(geolocation_point__within=bbox)
            .select_related("survey", "respondant")
            .prefetch_related(Prefetch("follow_up_responses", queryset=follow_up_qs))
            .order_by("-creation_date")
        )

        surveys_param = params.get("surveys", "").strip()
        if surveys_param:
            qs = qs.filter(survey_id__in=parse_ids(surveys_param, "surveys"))

        after_param = params.get("after", "").strip()
        if after_param:
            qs = qs.filter(creation_date__date__gte=parse_date(after_param, "after"))

        before_param = params.get("before", "").strip()
        if before_param:
            qs = qs.filter(creation_date__date__lte=parse_date(before_param, "before"))

        if params.get("only_mine", "").lower() == "true":
            qs = qs.filter(respondant=user)

        return qs[:GEO_RESPONSE_LIMIT]

    def _get_placettes(self, memberships, params, south, west, north, east):
        if not memberships:
            return Placette.objects.none()

        # Toutes les conditions d'accès ET de publication dans un seul Q par membership,
        # afin d'éviter des JOINs indépendants sur la table M2M qui pourraient satisfaire
        # des conditions via des protocoles différents (faux positifs).
        query = Q()
        for m in memberships:
            base = {"surveys__is_active": True, "surveys__is_published": True}
            if m.pole_id is None:
                query |= Q(surveys__organisation_id=m.organisation_id, **base)
            else:
                query |= Q(surveys__pole_id=m.pole_id, **base) | Q(
                    surveys__organisation_id=m.organisation_id,
                    surveys__pole__isnull=True,
                    **base,
                )

        # Q d'accès aux protocoles (pôle-aware), réutilisé pour le prefetch et le filtre.
        accessible_q = Q()
        for m in memberships:
            if m.pole_id is None:
                accessible_q |= Q(organisation_id=m.organisation_id)
            else:
                accessible_q |= Q(pole_id=m.pole_id) | Q(organisation_id=m.organisation_id, pole__isnull=True)

        surveys_prefetch = Prefetch(
            "surveys",
            queryset=PlacetteSurvey.objects.filter(accessible_q, is_active=True, is_published=True),
        )

        qs = (
            Placette.objects.active()
            .filter(query)
            .filter(lat__gte=south, lat__lte=north, lon__gte=west, lon__lte=east)
            .prefetch_related(surveys_prefetch)
            .distinct()
            .order_by("id")
        )

        placette_surveys_param = params.get("placette_surveys", "").strip()
        if placette_surveys_param:
            ids = set(parse_ids(placette_surveys_param, "placette_surveys"))
            # On ne garde que les IDs accessibles à l'utilisateur pour éviter qu'un JOIN M2M
            # indépendant permette de découvrir qu'une placette appartient à un protocole
            # d'une autre organisation (fuite d'information inter-org).
            accessible_ids = set(
                PlacetteSurvey.objects.filter(accessible_q, is_active=True, is_published=True, id__in=ids).values_list(
                    "id", flat=True
                )
            )
            if not accessible_ids:
                return Placette.objects.none()
            qs = qs.filter(surveys__id__in=accessible_ids)

        return qs[:GEO_PLACETTE_LIMIT]
