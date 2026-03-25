from django.db import models

from common.behaviours import Deactivable, TimeStampable

from .organisation import Organisation


class Pole(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "pôle"

    name = models.CharField("nom")
    organisation = models.ForeignKey(Organisation, related_name="poles", on_delete=models.CASCADE)
