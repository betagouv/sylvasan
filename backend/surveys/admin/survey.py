from django.contrib import admin

from surveys.models import Survey


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "organisation", "pole", "created_by")
