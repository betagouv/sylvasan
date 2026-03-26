from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import Survey


@admin.register(Survey)
class SurveyAdmin(SimpleHistoryAdmin):
    list_display = ("title", "organisation", "pole", "created_by")
