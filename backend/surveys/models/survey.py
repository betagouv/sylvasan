from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from common.behaviours import Deactivable, TimeStampable
from organisations.models import Organisation, Pole

from surveys.surveytype import SurveyType

from .campaign import Campaign


class Survey(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "enquête"

    organisation = models.ForeignKey(
        Organisation, related_name="surveys", on_delete=models.SET_NULL, null=True, blank=True
    )
    pole = models.ForeignKey(Pole, related_name="surveys", on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField("titre")
    json_schema = models.JSONField(verbose_name="schéma JSON", null=True, blank=True)

    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name="créateur ou créatrice",
        related_name="created_surveys",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    survey_type = models.CharField(choices=SurveyType, default=SurveyType.SELF_CONTAINED)

    campaign = models.ForeignKey(Campaign, verbose_name="campagne", on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if self.campaign:
            if self.organisation != self.campaign.organisation or self.pole != self.campaign.pole:
                raise ValidationError("La campagne doit appartenir à la même organisation/pôle que l'enquête.")
