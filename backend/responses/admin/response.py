from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from responses.models import Response


@admin.register(Response)
class ResponseAdmin(SimpleHistoryAdmin):
    list_display = ("survey_or_follow_up", "respondant", "status", "submission_date", "activity_icon")

    @admin.display(description="Enquête")
    def survey_or_follow_up(self, obj):
        if obj.survey_follow_up:
            return f"{obj.survey_follow_up.parent_survey} — {obj.survey_follow_up.title}"
        return obj.survey
