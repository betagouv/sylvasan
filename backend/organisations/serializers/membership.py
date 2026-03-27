from rest_framework import serializers

from organisations.models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ("organisation", "pole", "membership_type")
