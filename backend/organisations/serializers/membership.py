from rest_framework import serializers

from organisations.models import Membership

from .organisation import OrganisationSerializer
from .pole import PoleSerializer


class MembershipSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer()
    pole = PoleSerializer(allow_null=True)

    class Meta:
        model = Membership
        fields = ("organisation", "pole", "membership_type")
