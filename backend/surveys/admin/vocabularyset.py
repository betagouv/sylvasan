from django.contrib import admin

from surveys.models import VocabularySet


@admin.register(VocabularySet)
class VocabularySetAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organisation")
