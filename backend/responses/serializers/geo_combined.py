from rest_framework import serializers
from surveys.models import Placette
from users.serializers import UserDisplaySerializer

from responses.models import Response


class PlacetteObservationSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source="survey.title", read_only=True, allow_null=True)
    respondant = UserDisplaySerializer(read_only=True)

    class Meta:
        model = Response
        fields = ("id", "creation_date", "survey_title", "respondant")


class PlacetteGeoSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source="group.id", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    responses = PlacetteObservationSerializer(many=True, read_only=True)

    class Meta:
        model = Placette
        fields = ("id", "lat", "lon", "label", "group_id", "group_name", "characteristics", "responses")
