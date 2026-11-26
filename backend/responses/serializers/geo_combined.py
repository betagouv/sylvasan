from rest_framework import serializers
from surveys.models import Placette, PlacetteSurvey


class PlacetteSurveyMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacetteSurvey
        fields = ("id", "name")


class PlacetteGeoSerializer(serializers.ModelSerializer):
    survey = PlacetteSurveyMinimalSerializer(read_only=True)

    class Meta:
        model = Placette
        fields = ("id", "lat", "lon", "label", "survey", "characteristics")
