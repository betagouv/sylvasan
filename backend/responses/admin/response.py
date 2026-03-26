from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from responses.models import Response


@admin.register(Response)
class ResponseAdmin(SimpleHistoryAdmin):
    list_display = ("survey", "respondant", "status", "submission_date")
