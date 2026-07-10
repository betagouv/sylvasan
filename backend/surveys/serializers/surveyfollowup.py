from organisations.serializers import OrganisationSerializer, PoleSerializer
from rest_framework import serializers

from surveys.models import SurveyFollowUp


class SurveyFollowUpSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    pole = PoleSerializer(allow_null=True)

    class Meta:
        model = SurveyFollowUp
        fields = (
            "id",
            "organisation",
            "pole",
            "title",
            "json_schema",
            "action_label",
            "action_icon",
            "action_color",
            "created_by",
        )
        read_only_fields = ("id", "created_by")


class SurveyFollowUpWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyFollowUp
        fields = (
            "id",
            "organisation",
            "pole",
            "title",
            "json_schema",
            "action_label",
            "action_icon",
            "action_color",
            "created_by",
        )
        read_only_fields = ("id", "created_by")
