from django.db.models import Prefetch

from organisations.models import Organisation, Pole
from organisations.serializers import MembershipSerializer
from organisations.serializers.organisation import FullOrganisationSerializer
from rest_framework import serializers

from users.models import User


class UserDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
        )


class SimpleUserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    organisations = serializers.SerializerMethodField()

    def get_organisations(self, obj):
        orgs = (
            Organisation.objects.filter(memberships__user=obj)
            .distinct()
            .prefetch_related(Prefetch("poles", queryset=Pole.objects.filter(is_active=True).order_by("name")))
        )
        return FullOrganisationSerializer(orgs, many=True).data

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "memberships",
            "organisations",
            "source",
        )
