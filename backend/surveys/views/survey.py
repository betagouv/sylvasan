from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from surveys.models import Survey
from surveys.permissions import CanCreateSurvey
from surveys.serializers import SurveySerializer


class SurveyCreateAPIView(CreateAPIView):
    model = Survey
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated, CanCreateSurvey]
