from django.core.exceptions import ValidationError
from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable

from .placette import Placette
from .placettelevel import PlacetteLevel


class PlacetteNode(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "nœud de placette"
        verbose_name_plural = "nœuds de placettes"

    objects = DeactivableQuerySet.as_manager()

    placette = models.ForeignKey(Placette, related_name="nodes", on_delete=models.CASCADE)
    level = models.ForeignKey(PlacetteLevel, related_name="nodes", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    label = models.CharField("libellé", blank=True, default="")
    lat = models.FloatField("latitude", null=True, blank=True)
    lon = models.FloatField("longitude", null=True, blank=True)

    def clean(self):
        if (
            self.level_id
            and self.placette_id
            and not self.placette.surveys.filter(pk=self.level.placette_survey_id).exists()
        ):
            raise ValidationError("Le niveau de ce nœud appartient à un protocole non assigné à cette placette.")
        if self.parent_id and self.level_id:
            if self.placette_id and self.parent.placette_id != self.placette_id:
                raise ValidationError("Le nœud parent doit appartenir à la même placette.")
            if self.level.parent_level_id is None:
                raise ValidationError("Un nœud de niveau racine ne peut pas avoir de nœud parent.")
            if self.level.parent_level_id != self.parent.level_id:
                raise ValidationError("Le niveau du nœud parent ne correspond pas au niveau parent attendu.")
        elif self.level_id and self.level.parent_level_id is not None:
            raise ValidationError("Un nœud de niveau non-racine doit avoir un nœud parent.")

    def __str__(self):
        return f"{self.label or self.id} ({self.placette})"
