from django.contrib import admin

from surveys.models import VocabularyEntry

VocabularyEntry._meta.verbose_name = "entrée de référentiel"
VocabularyEntry._meta.verbose_name_plural = "entrées des référentiels"


@admin.register(VocabularyEntry)
class VocabularyEntryAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "vocabulary_set", "position")
