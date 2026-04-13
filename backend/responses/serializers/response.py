from rest_framework import serializers
from surveys.serializers import FullSurveySerializer, SurveyDisplaySerializer
from users.serializers import UserDisplaySerializer

from responses.models import Response


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",  # TODO : devrait être peuplé automatiquement
            "data",
            "context",
            "status",
        )
        read_only_fields = ("id", "status")


class ResponseDisplaySerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = SurveyDisplaySerializer(read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",
            "status",
            "creation_date",
        )
        read_only_fields = fields


class FullResponseSerializer(serializers.ModelSerializer):
    respondant = UserDisplaySerializer(read_only=True)
    survey = FullSurveySerializer(read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",
            "data",
            "context",
            "status",
            "creation_date",
        )
        read_only_fields = fields
