from organisations.models import Organisation
from rest_framework import serializers

from surveys.models import VocabularyEntry, VocabularySet


class VocabularyEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyEntry
        fields = ("id", "code", "label", "position")


class VocabularySetDisplaySerializer(serializers.ModelSerializer):
    """Sans les entrées — pour les listes."""

    class Meta:
        model = VocabularySet
        fields = ("id", "code", "name")


class VocabularySetSerializer(serializers.ModelSerializer):
    entries = VocabularyEntrySerializer(many=True, read_only=True)
    organisation_name = serializers.CharField(source="organisation.name", read_only=True, allow_null=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), write_only=True)

    class Meta:
        model = VocabularySet
        fields = ("id", "code", "name", "entries", "organisation_name", "organisation")
