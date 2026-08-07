from rest_framework import serializers
from users.serializers import UserDisplaySerializer

from responses.models import Response


class GeoFollowUpSerializer(serializers.ModelSerializer):
    survey = serializers.SerializerMethodField()
    respondant = UserDisplaySerializer(read_only=True)

    class Meta:
        model = Response
        fields = ("id", "creation_date", "survey", "respondant")

    def get_survey(self, obj):
        follow_up = obj.survey_follow_up
        if not follow_up:
            return None
        return {
            "title": follow_up.title,
            "action_color": follow_up.action_color,
            "action_icon": follow_up.action_icon,
        }


class GeoResponseSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    survey_title = serializers.SerializerMethodField()
    respondant = UserDisplaySerializer(read_only=True)
    follow_ups = GeoFollowUpSerializer(many=True, source="follow_up_responses", read_only=True)

    class Meta:
        model = Response
        fields = (
            "id",
            "survey_id",
            "survey_title",
            "status",
            "creation_date",
            "lat",
            "lon",
            "respondant",
            "follow_ups",
        )

    def get_lat(self, obj):
        return obj.geolocation_point.y

    def get_lon(self, obj):
        return obj.geolocation_point.x

    def get_survey_title(self, obj):
        return obj.survey.title if obj.survey else None
