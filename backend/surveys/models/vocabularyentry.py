from django.db import models

from .vocabularyset import VocabularySet


class VocabularyEntry(models.Model):
    class Meta:
        verbose_name = "entrée de vocabulaire"
        unique_together = ("vocabulary_set", "code")

    vocabulary_set = models.ForeignKey(VocabularySet, related_name="entries", on_delete=models.CASCADE)
    code = models.CharField(max_length=255)
    label = models.TextField()
    position = models.IntegerField(null=True, blank=True)
