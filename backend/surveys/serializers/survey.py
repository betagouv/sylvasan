from rest_framework import serializers

from surveys.models import Survey


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = (
            "id",
            "organisation",
            "pole",
            "title",
            "json_schema",
            "survey_type",
            "campaign",
            "created_by",  # TODO : ça devrait être peuplé automatiquement
        )
        read_only_fields = ("id",)
