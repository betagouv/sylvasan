from rest_framework import serializers

from organisations.models import Pole


class PoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pole
        fields = ("id", "name")
