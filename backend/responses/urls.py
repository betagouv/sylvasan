from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

import responses.views as views

urlpatterns = [
    path("api/responses/", views.ResponseListCreateAPIView.as_view(), name="response_list_create"),
    path("api/responses/<int:pk>", views.ResponseRetrieveAPIView.as_view(), name="response_retrieve"),
    path("api/responses/export/json/", views.ResponseJsonExportView.as_view(), name="response_export_json"),
    path("api/responses/export/csv/", views.ResponseCsvExportView.as_view(), name="response_export_csv"),
    path("api/mobile/responses/", views.ResponseFullListAPIView.as_view(), name="response_responder_retrieve"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
