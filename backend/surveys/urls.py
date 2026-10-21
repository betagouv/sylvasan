from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from surveys import views

urlpatterns = [
    path("api/surveys/", views.SurveyListCreateAPIView.as_view(), name="survey_list_create"),
    path(
        "api/surveys/<int:pk>",
        views.SurveyRetrieveUpdateDestroyAPIView.as_view(),
        name="survey_retrieve_update_destroy",
    ),
    path(
        "api/surveys/<int:survey_pk>/follow-ups",
        views.SurveyFollowUpListCreateAPIView.as_view(),
        name="follow_up_list_create",
    ),
    path(
        "api/surveys/<int:survey_pk>/follow-ups/<int:pk>",
        views.SurveyFollowUpRetrieveUpdateDestroyAPIView.as_view(),
        name="follow_up_retrieve_update_destroy",
    ),
    path("api/mobile/surveys/", views.SurveyResponderListAPIView.as_view(), name="survey_responder_retrieve"),
    path("api/admin/vocabularies/", views.VocabularySetListView.as_view(), name="vocabulary_set_list"),
    path(
        "api/admin/vocabularies/<int:pk>/", views.VocabularySetRetrieveView.as_view(), name="vocabulary_retrieve_view"
    ),
    path(
        "api/admin/vocabularies/<int:vocabularyset_pk>/entries/<int:pk>/",
        views.VocabularyEntryAdminView.as_view(),
        name="vocabulary_entry_admin_view",
    ),
    path("api/vocabularies/<str:code>/", views.VocabularySetDetailView.as_view(), name="vocabulary_set_detail"),
    path("api/mobile/vocabularies/", views.MobileVocabularySetListView.as_view(), name="mobile_vocabulary_set_list"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
