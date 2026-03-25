from django.contrib import admin

from surveys.models import VocabularyEntry


@admin.register(VocabularyEntry)
class VocabularyEntryAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "vocabulary_set", "position")
