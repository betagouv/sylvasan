from django.contrib.auth import get_user_model
from django.db import models

from common.behaviours import Historisable, TimeStampable
from surveys.models import Survey


class ResponseStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    SUBMITTED = "submitted", "Envoyé"
    EXPORTED = "exported", "Exporté"


class Response(TimeStampable, Historisable):
    survey = models.ForeignKey(Survey, related_name="responses", verbose_name="enquête", on_delete=models.CASCADE)
    respondant = models.ForeignKey(
        get_user_model(),
        related_name="responses",
        verbose_name="répondant ou répondante",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(choices=ResponseStatus, verbose_name="statut", default=ResponseStatus.SUBMITTED)
    data = models.JSONField(verbose_name="données")
    submission_date = models.DateTimeField(null=True, blank=True, verbose_name="date de soumission")

    # Pour des informations supplémentaires nécessaires dans des enquêtes plus complexes. Par
    # example, on pourrait avoir ici les arbres assignés à une personne
    context = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.survey} – {self.get_status_display()}"
