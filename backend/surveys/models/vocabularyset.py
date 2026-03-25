from django.db import models

from organisations.models import Organisation


class VocabularySet(models.Model):
    class Meta:
        verbose_name = "set de vocabulaire"
        unique_together = ("organisation", "code")

    organisation = models.ForeignKey(
        Organisation, related_name="vocabularies", on_delete=models.SET_NULL, null=True, blank=True
    )
    code = models.CharField(max_length=255)
    name = models.TextField()
