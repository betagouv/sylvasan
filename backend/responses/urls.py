from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from responses import views

urlpatterns = [
    path("api/responses/", views.ResponseListCreateAPIView.as_view(), name="response_list_create"),
    path("api/responses/export/json/", views.ResponseJsonExportView.as_view(), name="response_export_json"),
    path("api/responses/export/csv/", views.ResponseCsvExportView.as_view(), name="response_export_csv"),
    path("api/responses/images/<int:org_id>/", views.ResponseImagesListView.as_view(), name="response_images_list"),
    path("api/mobile/responses/", views.ResponseFullListAPIView.as_view(), name="response_responder_retrieve"),
    path("api/mobile/responses/geo/", views.ResponseGeoListAPIView.as_view(), name="response_geo_list"),
    path("api/responses/<int:pk>", views.ResponseRetrieveDestroyAPIView.as_view(), name="response_retrieve_destroy"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
