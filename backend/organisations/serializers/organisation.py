from rest_framework import serializers

from organisations.models import Organisation, Pole


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name")


class FullPoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pole
        fields = ("id", "name")


class FullOrganisationSerializer(serializers.ModelSerializer):
    poles = FullPoleSerializer(many=True, read_only=True)

    class Meta:
        model = Organisation
        fields = ("id", "name", "poles")
