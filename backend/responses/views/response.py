from django.db.models import Q
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from organisations.models import Membership, MembershipType
from responses.models import Response
from responses.permissions import CanCreateResponse
from responses.serializers import ResponseDisplaySerializer, ResponseSerializer


class ResponseListCreateAPIView(ListCreateAPIView):
    serializer_class = ResponseSerializer

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ResponseDisplaySerializer
        return ResponseSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateResponse()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        memberships = Membership.objects.filter(user=user)

        if not memberships.exists():
            return Response.objects.none()

        query = Q()
        for membership in memberships:
            if membership.membership_type == MembershipType.RESPONDER:
                query |= Q(respondant=user)
            elif membership.pole is not None:
                query |= Q(survey__pole=membership.pole)
            else:
                query |= Q(survey__organisation=membership.organisation)

        return Response.objects.filter(query).distinct()
