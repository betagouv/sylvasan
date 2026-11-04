from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable

from .placettesurvey import PlacetteSurvey


class Placette(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "placette"

    objects = DeactivableQuerySet.as_manager()

    surveys = models.ManyToManyField(PlacetteSurvey, related_name="placettes", blank=True)
    label = models.CharField("libellé")
    lat = models.FloatField("latitude")
    lon = models.FloatField("longitude")
    characteristics = models.JSONField("caractéristiques", default=dict, blank=True)
    # Identifiants DSF (nullables : placettes créées dans Sylvasan avant import).
    dsf_id_localisation = models.IntegerField("identifiant DSF localisation", null=True, blank=True, unique=True)
    code = models.CharField("code placette", max_length=50, null=True, blank=True)

    def __str__(self):
        return self.label
