from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import SurveyFollowUp


@admin.register(SurveyFollowUp)
class SurveyFollowUpAdmin(SimpleHistoryAdmin):
    list_display = ("title", "parent_survey", "organisation", "pole", "created_by", "is_active")
    list_filter = ("organisation", "is_active")
    search_fields = ("title", "parent_survey__title")
