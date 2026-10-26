from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable
from organisations.models import Organisation, Pole


class PlacetteGroup(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "groupe de placettes"
        verbose_name_plural = "groupes de placettes"

    objects = DeactivableQuerySet.as_manager()

    name = models.CharField("nom")
    organisation = models.ForeignKey(
        Organisation,
        related_name="placette_groups",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    pole = models.ForeignKey(
        Pole,
        related_name="placette_groups",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_published = models.BooleanField(
        "publié",
        default=False,
        help_text="Si activé, le groupe est visible par les répondants.",
    )

    def __str__(self):
        return self.name
