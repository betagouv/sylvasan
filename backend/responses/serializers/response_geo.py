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
        sfu = obj.survey_follow_up
        if not sfu:
            return None
        return {
            "title": sfu.title,
            "action_color": sfu.action_color,
            "action_icon": sfu.action_icon,
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
