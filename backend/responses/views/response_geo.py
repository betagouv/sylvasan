from typing import ClassVar

from django.contrib.gis.geos import Polygon
from django.db.models import Prefetch, Q

from organisations.models import Membership
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from responses.models import Response
from responses.serializers.response_geo import GeoResponseSerializer
from responses.utils import parse_date, parse_ids, validate_bbox

GEO_RESPONSE_LIMIT = 200


class ResponseGeoListAPIView(ListAPIView):
    """
    Retourne les réponses géolocalisées dans la zone de la carte.

    Paramètres obligatoires (degrés décimaux WGS-84) :
        south, west, north, east

    Paramètres optionnels de filtrage :
        surveys     — identifiants d'enquêtes séparés par des virgules (ex: 12,13,15)
        after       — date de création minimale, incluse (format YYYY-MM-DD)
        before      — date de création maximale, incluse (format YYYY-MM-DD)
        only_mine   — "true" pour ne voir que ses propres réponses

    Les résultats sont filtrés selon les droits de l'utilisateur·ice connecté·e :
    les membres d'une organisation voient toutes les réponses de cette organisation
    dans la zone, qu'ils en soient l'auteur ou non.

    Le nombre de résultats est plafonné à GEO_RESPONSE_LIMIT pour éviter
    de surcharger la mémoire de l'application mobile.
    """

    serializer_class = GeoResponseSerializer
    permission_classes: ClassVar = [IsAuthenticated]
    pagination_class = None
    filter_backends: ClassVar = []

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        south, west, north, east = validate_bbox(params)

        bbox = Polygon.from_bbox((west, south, east, north))
        bbox.srid = 4326

        memberships = list(Membership.objects.filter(user=user))
        if not memberships:
            return Response.objects.none()

        query = Q()
        for membership in memberships:
            org_id = membership.organisation_id
            pole_id = membership.pole_id
            if pole_id is None:
                # Accès à toutes les enquêtes de l'organisation
                query |= Q(survey__organisation_id=org_id)
            else:
                # Accès aux enquêtes du pôle et aux enquêtes sans pôle de l'organisation
                query |= Q(survey__pole_id=pole_id) | Q(
                    survey__organisation_id=org_id,
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

        # Filtre par identifiants d'enquêtes
        surveys_param = params.get("surveys", "").strip()
        if surveys_param:
            qs = qs.filter(survey_id__in=parse_ids(surveys_param, "surveys"))

        # Filtre par date de création (after / before, dates incluses)
        after_param = params.get("after", "").strip()
        if after_param:
            qs = qs.filter(creation_date__date__gte=parse_date(after_param, "after"))

        before_param = params.get("before", "").strip()
        if before_param:
            qs = qs.filter(creation_date__date__lte=parse_date(before_param, "before"))

        # Filtre « mes observations uniquement »
        if params.get("only_mine", "").lower() == "true":
            qs = qs.filter(respondant=user)

        return qs[:GEO_RESPONSE_LIMIT]
