from organisations.serializers import OrganisationSerializer, PoleSerializer
from rest_framework import serializers

from surveys.models import Survey

from .surveyfollowup import SurveyFollowUpSerializer


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
            "created_by",
        )
        read_only_fields = ("id", "created_by")


class FullSurveySerializer(serializers.ModelSerializer):
    follow_ups = serializers.SerializerMethodField()
    organisation = OrganisationSerializer()
    pole = PoleSerializer(allow_null=True)

    def get_follow_ups(self, obj):
        return SurveyFollowUpSerializer(obj.follow_ups.filter(is_active=True), many=True).data

    class Meta:
        model = Survey
        fields = (
            "id",
            "organisation",
            "follow_ups",
            "pole",
            "title",
            "json_schema",
            "survey_type",
            "campaign",
            "created_by",  # TODO : ça devrait être peuplé automatiquement
        )
        read_only_fields = ("id",)
