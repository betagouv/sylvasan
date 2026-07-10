from organisations.serializers import OrganisationSerializer, PoleSerializer
from rest_framework import serializers

from surveys.models import Survey


class SurveyFollowUpSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    pole = PoleSerializer(allow_null=True)

    class Meta:
        model = Survey
        fields = (
            "id",
            "organisation",
            "pole",
            "title",
            "json_schema",
            "action_label",
            "action_icon",
            "action_color",
            "created_by",  # TODO : ça devrait être peuplé automatiquement
        )
        read_only_fields = ("id", "created_by")
