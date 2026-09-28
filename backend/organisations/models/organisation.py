from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.behaviours import Deactivable, TimeStampable


class Organisation(TimeStampable, Deactivable):
    name = models.CharField("nom")
    vocabulary_categories = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
        verbose_name="catégories de vocabulaire accessibles",
    )

    def __str__(self):
        return self.name
