from typing import ClassVar

from django.db.models import Prefetch, Q

from organisations.models import Membership
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView
from surveys.models import Placette

from responses.models import Response
from responses.models import Response as ResponseModel
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
        surveys          — identifiants d'enquêtes séparés par des virgules
        placette_groups  — identifiants de groupes de placettes séparés par des virgules
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

        query = Q()
        for m in memberships:
            if m.pole_id is None:
                query |= Q(group__organisation_id=m.organisation_id)
            else:
                query |= Q(group__pole_id=m.pole_id) | Q(
                    group__organisation_id=m.organisation_id,
                    group__pole__isnull=True,
                )

        obs_qs = ResponseModel.objects.active().select_related("survey", "respondant").order_by("-creation_date")

        qs = (
            Placette.objects.active()
            .filter(query)
            .filter(
                group__is_active=True,
                group__is_published=True,
                lat__gte=south,
                lat__lte=north,
                lon__gte=west,
                lon__lte=east,
            )
            .select_related("group")
            .prefetch_related(Prefetch("responses", queryset=obs_qs))
        )

        placette_groups_param = params.get("placette_groups", "").strip()
        if placette_groups_param:
            qs = qs.filter(group_id__in=parse_ids(placette_groups_param, "placette_groups"))

        return qs[:GEO_PLACETTE_LIMIT]
