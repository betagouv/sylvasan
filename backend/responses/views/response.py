from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from responses.models import Response
from responses.permissions import CanCreateResponse
from responses.serializers import ResponseSerializer


class ResponseCreateAPIView(CreateAPIView):
    model = Response
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated, CanCreateResponse]
