from rest_framework import serializers

from responses.models import Response


class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = (
            "id",
            "survey",
            "respondant",  # TODO : devrait être peuplé automatiquement
            "data",
            "context",
            "status",
        )
        read_only_fields = ("id", "status")
