from django.contrib import admin

from responses.models import Response


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "respondant", "status", "submission_date")
