import logging

from django.contrib.auth import get_user_model
from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, Historisable, TimeStampable
from surveys.models import Survey, SurveyFollowUp

logger = logging.getLogger(__name__)


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

    geolocation_point = PointField(null=True, blank=True, verbose_name="Localisation")

    def _populate_geolocation(self):
        from django.contrib.gis.geos import Point

        try:
            survey = self.survey
            if survey is None or not isinstance(getattr(survey, "json_schema", None), dict):
                self.geolocation_point = None
                return

            map_field = next(
                (
                    f
                    for f in survey.json_schema.get("fields", [])
                    if isinstance(f, dict) and f.get("ui", {}).get("widget") == "map"
                ),
                None,
            )
            if map_field is None:
                self.geolocation_point = None
                return

            field_id = map_field.get("id")
            if not field_id:
                self.geolocation_point = None
                return

            data = self.data
            value = data.get(field_id) if isinstance(data, dict) else None
            if not isinstance(value, dict):
                self.geolocation_point = None
                return

            lat = value.get("lat")
            lon = value.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                self.geolocation_point = Point(lon, lat, srid=4326)
            else:
                self.geolocation_point = None
        except Exception:
            logger.exception("Error setting geopoint to response object")

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is None or any(f in update_fields for f in ("data", "survey", "survey_id")):
            self._populate_geolocation()
            if update_fields is not None and "geolocation_point" not in update_fields:
                kwargs["update_fields"] = list(update_fields) + ["geolocation_point"]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.survey or self.survey_follow_up} – {self.get_status_display()}"

    def clean(self):
        if bool(self.survey) and bool(self.survey_follow_up):
            raise ValidationError("Une réponse doit avoir soit une enquête, soit un suivi, pas les deux.")
        if self.survey_follow_up and not self.parent_response:
            raise ValidationError("Une réponse de suivi doit référencer une réponse parente.")


class ResponseImage(TimeStampable):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="images")
    file = models.ImageField(upload_to="response_images/%Y/%m/")
    thumbnail = models.ImageField(upload_to="response_thumbnails/%Y/%m/")
