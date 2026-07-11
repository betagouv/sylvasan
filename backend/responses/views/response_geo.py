from django.contrib.gis.geos import Polygon
from django.db.models import Q

from organisations.models import Membership
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from responses.models import Response
from responses.serializers.response_geo import GeoResponseSerializer

GEO_RESPONSE_LIMIT = 200


class ResponseGeoListAPIView(ListAPIView):
    """
    Retourne les réponses géolocalisées dans la zone de la carte.

    Paramètres obligatoires (degrés décimaux WGS-84) :
        south, west, north, east

    Les résultats sont filtrés selon les droits de l'utilisateur·ice connecté·e :
    les membres d'une organisation voient toutes les réponses de cette organisation
    dans la zone, qu'ils en soient l'auteur ou non.

    Le nombre de résultats est plafonné à GEO_RESPONSE_LIMIT pour éviter
    de surcharger la mémoire de l'application mobile.
    """

    serializer_class = GeoResponseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = []

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        try:
            south = float(params["south"])
            west = float(params["west"])
            north = float(params["north"])
            east = float(params["east"])
        except (KeyError, ValueError):
            raise ValidationError(
                "Les paramètres south, west, north et east sont obligatoires et doivent être des nombres."
            )

        if south >= north:
            raise ValidationError("south doit être strictement inférieur à north.")

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

        return (
            Response.objects.active()
            .filter(query)
            .filter(geolocation_point__within=bbox)
            .select_related("survey")
            .order_by("-creation_date")[:GEO_RESPONSE_LIMIT]
        )
