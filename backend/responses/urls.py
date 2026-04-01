from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

import responses.views as views

urlpatterns = [
    path("api/responses/", views.ResponseListCreateAPIView.as_view(), name="response_list_create"),
    path("api/responses/<int:pk>", views.ResponseRetrieveAPIView.as_view(), name="response_retrieve"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
