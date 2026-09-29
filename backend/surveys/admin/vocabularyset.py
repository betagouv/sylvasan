from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from surveys.models import VocabularySet

VocabularySet._meta.verbose_name = "référentiel"
VocabularySet._meta.verbose_name_plural = "référentiels"


@admin.register(VocabularySet)
class VocabularySetAdmin(SimpleHistoryAdmin):
    list_display = ("code", "name", "category", "organisation", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("code", "name")
