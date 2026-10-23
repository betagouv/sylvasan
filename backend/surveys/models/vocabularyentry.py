from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet

from .vocabularyset import VocabularySet


class VocabularyEntry(Deactivable):
    class Meta:
        verbose_name = "entrée de vocabulaire"
        unique_together = ("vocabulary_set", "code")

    objects = DeactivableQuerySet.as_manager()

    vocabulary_set = models.ForeignKey(VocabularySet, related_name="entries", on_delete=models.CASCADE)
    code = models.CharField()
    label = models.CharField()
    position = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.label} ({self.code})"
