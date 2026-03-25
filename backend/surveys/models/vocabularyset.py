from django.db import models

from organisations.models import Organisation


class VocabularySet(models.Model):
    class Meta:
        verbose_name = "set de vocabulaire"
        unique_together = ("organisation", "code")

    organisation = models.ForeignKey(
        Organisation, related_name="vocabularies", on_delete=models.SET_NULL, null=True, blank=True
    )
    code = models.CharField()
    name = models.CharField("nom")

    def __str__(self):
        return f"{self.name} ({self.code})"
