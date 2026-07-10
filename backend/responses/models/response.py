from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, Historisable, TimeStampable
from surveys.models import Survey, SurveyFollowUp


class ResponseStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    SUBMITTED = "submitted", "Envoyé"
    EXPORTED = "exported", "Exporté"


class Response(TimeStampable, Historisable, Deactivable):
    objects = DeactivableQuerySet.as_manager()

    survey = models.ForeignKey(
        Survey,
        related_name="responses",
        verbose_name="enquête",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    survey_follow_up = models.ForeignKey(
        SurveyFollowUp,
        related_name="responses",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    parent_response = models.ForeignKey(
        "self",
        related_name="follow_up_responses",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

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

    def clean(self):
        if bool(self.survey) and bool(self.survey_follow_up):
            raise ValidationError("Une réponse doit avoir soit une enquête, soit un suivi, pas les deux.")
        if self.survey_follow_up and not self.parent_response:
            raise ValidationError("Une réponse de suivi doit référencer une réponse parente.")


class ResponseImage(TimeStampable):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="images")
    file = models.ImageField(upload_to="response_images/%Y/%m/")
    thumbnail = models.ImageField(upload_to="response_thumbnails/%Y/%m/")
