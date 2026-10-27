from rest_framework import serializers
from surveys.models import Placette


class PlacetteGeoSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source="group.id", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Placette
        fields = ("id", "lat", "lon", "label", "group_id", "group_name", "characteristics")
