from rest_framework import serializers

from surveys.models import VocabularyEntry, VocabularySet


class VocabularyEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyEntry
        fields = ("code", "label", "position")


class VocabularySetSerializer(serializers.ModelSerializer):
    entries = VocabularyEntrySerializer(many=True, read_only=True)

    class Meta:
        model = VocabularySet
        fields = ("id", "code", "name", "entries")
