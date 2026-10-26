from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable

from .placettegroup import PlacetteGroup


class Placette(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "placette"

    objects = DeactivableQuerySet.as_manager()

    group = models.ForeignKey(PlacetteGroup, related_name="placettes", on_delete=models.CASCADE)
    label = models.CharField("libellé")
    lat = models.FloatField("latitude")
    lon = models.FloatField("longitude")
    characteristics = models.JSONField("caractéristiques", default=dict, blank=True)

    def __str__(self):
        return f"{self.label} ({self.group})"
