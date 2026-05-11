from django.db import models

from common.behaviours import Deactivable, TimeStampable

from .organisation import Organisation


class Pole(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "pôle"

    name = models.CharField("nom")
    organisation = models.ForeignKey(Organisation, related_name="poles", on_delete=models.CASCADE)
    dsf_code = models.CharField(max_length=12, blank=True, null=True, verbose_name="Code IGN/DSF")

    def __str__(self):
        return self.name
