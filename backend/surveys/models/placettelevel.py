from typing import ClassVar

from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable

from .placettesurvey import PlacetteSurvey


class PlacetteLevel(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "niveau de placette"
        verbose_name_plural = "niveaux de placettes"
        ordering: ClassVar = ["order"]
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["placette_survey", "key"], name="unique_level_key_per_survey"),
        ]

    objects = DeactivableQuerySet.as_manager()

    placette_survey = models.ForeignKey(PlacetteSurvey, related_name="levels", on_delete=models.CASCADE)
    # parent_level=None : niveau racine du protocole. Son json_schema contient les champs saisis
    # à la racine (avant tout nœud enfant). Les niveaux enfants définissent les champs
    # de chaque instance (arbre, branche, échantillon…).
    parent_level = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField("nom")
    # Clé stable (slug) unique au sein du protocole. Sert de clé dans Response.data
    # à la place de l'identifiant entier, qui change d'un environnement à l'autre.
    key = models.SlugField("clé", max_length=50, null=True, blank=True)
    json_schema = models.JSONField("schéma JSON", null=True, blank=True)
    has_coordinates = models.BooleanField("a des coordonnées", default=False)
    min_instances = models.PositiveIntegerField("nombre min d'instances", null=True, blank=True)
    max_instances = models.PositiveIntegerField("nombre max d'instances", null=True, blank=True)
    order = models.PositiveIntegerField("ordre", default=0)

    def __str__(self):
        return f"{self.name} ({self.placette_survey})"
