from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, Historisable, TimeStampable
from organisations.models import Organisation, Pole

from .survey import Survey


class SurveyFollowUp(TimeStampable, Deactivable, Historisable):
    class Meta:
        verbose_name = "suivi"

    objects = DeactivableQuerySet.as_manager()

    parent_survey = models.ForeignKey(Survey, related_name="follow_ups", on_delete=models.CASCADE)

    organisation = models.ForeignKey(
        Organisation, related_name="survey_follow_ups", on_delete=models.SET_NULL, null=True, blank=True
    )
    pole = models.ForeignKey(Pole, related_name="survey_follow_ups", on_delete=models.SET_NULL, null=True, blank=True)

    json_schema = models.JSONField(verbose_name="schéma JSON", null=True, blank=True)

    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name="créateur ou créatrice",
        related_name="created_survey_follow_ups",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    title = models.CharField("titre")

    # Données pour la UI
    action_label = models.CharField(blank=True)
    action_icon = models.CharField(max_length=50, blank=True)
    action_color = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.action_label} ({self.parent_survey})"

    def clean(self):
        if self.pole and self.organisation:
            if self.pole.organisation != self.organisation:
                raise ValidationError("Le pôle doit appartenir à l'organisation de l'enquête.")
