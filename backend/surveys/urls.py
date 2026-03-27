from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

import surveys.views as views

urlpatterns = {
    path("api/surveys/", views.SurveyListCreateAPIView.as_view(), name="survey_list_create"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
