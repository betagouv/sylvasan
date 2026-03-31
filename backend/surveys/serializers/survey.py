from rest_framework import serializers

from surveys.models import Survey


class SurveyDisplaySerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="organisation.name", allow_null=True)
    pole_name = serializers.CharField(source="pole.name", allow_null=True)
    campaign_title = serializers.CharField(source="campaigne.title", allow_null=True)

    class Meta:
        model = Survey
        fields = (
            "id",
            "organisation_name",
            "pole_name",
            "title",
            "campaign_title",
            "creation_date",
        )
        read_only_fields = fields


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
