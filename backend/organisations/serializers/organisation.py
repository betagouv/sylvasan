from rest_framework import serializers

from organisations.models import Organisation
from organisations.serializers.pole import PoleSerializer


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name")


class FullOrganisationSerializer(serializers.ModelSerializer):
    poles = PoleSerializer(many=True, read_only=True)

    class Meta:
        model = Organisation
        fields = ("id", "name", "poles")
