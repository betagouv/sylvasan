from rest_framework import serializers
from surveys.models import Placette, PlacetteSurvey


class PlacetteSurveyMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacetteSurvey
        fields = ("id", "name")


class PlacetteGeoSerializer(serializers.ModelSerializer):
    placette_surveys = PlacetteSurveyMinimalSerializer(source="surveys", many=True, read_only=True)

    class Meta:
        model = Placette
        fields = ("id", "lat", "lon", "label", "placette_surveys", "characteristics")
