from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import VocabularySet


@admin.register(VocabularySet)
class VocabularySetAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name", "organisation")
