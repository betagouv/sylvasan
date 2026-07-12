from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import Survey, SurveyFollowUp


class SurveyFollowUpInline(admin.TabularInline):
    model = SurveyFollowUp
    extra = 0
    fields = ("title", "organisation", "pole", "action_label", "action_icon", "action_color", "is_active")
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(SimpleHistoryAdmin):
    list_display = ("title", "organisation", "pole", "created_by", "creation_date", "activity_icon")
    inlines = [SurveyFollowUpInline]
