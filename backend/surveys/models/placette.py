from django.conf import settings
from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable
from organisations.models import Pole

from .placettesurvey import PlacetteSurvey


class Placette(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "placette"

    objects = DeactivableQuerySet.as_manager()

    survey = models.ForeignKey(
        PlacetteSurvey,
        verbose_name="enquête",
        related_name="placettes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    label = models.CharField("libellé")
    lat = models.FloatField("latitude")
    lon = models.FloatField("longitude")
    characteristics = models.JSONField("caractéristiques", default=dict, blank=True)
    # Identifiants DSF (nullables : placettes créées dans Sylvasan avant import).
    dsf_id_localisation = models.IntegerField("identifiant DSF localisation", null=True, blank=True)
    code = models.CharField("code placette", max_length=50, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="créateur",
        related_name="created_placettes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    accessors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="utilisateurs avec accès",
        related_name="accessible_placettes",
        blank=True,
    )
    pole = models.ForeignKey(
        Pole,
        verbose_name="pôle",
        related_name="placettes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.label
