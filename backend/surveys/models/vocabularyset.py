from django.db import models

from common.behaviours import Historisable
from organisations.models import Organisation


class VocabularyCategory(models.TextChoices):
    FOREST = "forest", "Forêt"


class VocabularySet(Historisable):
    class Meta:
        verbose_name = "set de vocabulaire"
        unique_together = ("category", "code")

    organisation = models.ForeignKey(
        Organisation, related_name="vocabularies", on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.CharField(
        "catégorie",
        max_length=50,
        choices=VocabularyCategory.choices,
        null=True,
        blank=True,
    )
    code = models.CharField()
    name = models.CharField("nom")
    is_active = models.BooleanField("actif", default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
