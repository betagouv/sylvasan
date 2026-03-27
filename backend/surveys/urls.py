from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

import surveys.views as views

urlpatterns = {
    path("api/surveys/", views.SurveyCreateAPIView.as_view(), name="create_survey"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
