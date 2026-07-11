from rest_framework import serializers

from responses.models import Response


class GeoResponseSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    survey_title = serializers.SerializerMethodField()

    class Meta:
        model = Response
        fields = ("id", "survey_id", "survey_title", "status", "creation_date", "lat", "lon")
        read_only_fields = fields

    def get_lat(self, obj):
        return obj.geolocation_point.y

    def get_lon(self, obj):
        return obj.geolocation_point.x

    def get_survey_title(self, obj):
        return obj.survey.title if obj.survey else None
