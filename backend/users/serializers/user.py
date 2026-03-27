from rest_framework import serializers

from organisations.serializers import MembershipSerializer
from users.models import User


class SimpleUserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", "memberships")
