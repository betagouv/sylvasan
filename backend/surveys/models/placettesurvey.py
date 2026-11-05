from django.db import models

from common.behaviours import Deactivable, DeactivableQuerySet, TimeStampable
from organisations.models import Organisation, Pole


def _level_to_fields(level, children_by_parent):
    fields = []
    if level.json_schema:
        fields.extend(level.json_schema.get("fields", []))
    for child in children_by_parent.get(level.id, []):
        child_fields = [{"id": "node_id", "type": "string", "label": "ID"}]
        child_fields.extend(_level_to_fields(child, children_by_parent))
        fields.append(
            {
                "id": child.key or str(child.id),
                "type": "array",
                "label": child.name,
                "fields": child_fields,
            }
        )
    return fields


class PlacetteSurvey(TimeStampable, Deactivable):
    class Meta:
        verbose_name = "protocole placette"
        verbose_name_plural = "protocoles placettes"

    objects = DeactivableQuerySet.as_manager()

    name = models.CharField("nom")
    organisation = models.ForeignKey(
        Organisation,
        related_name="placette_surveys",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    pole = models.ForeignKey(
        Pole,
        related_name="placette_surveys",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_published = models.BooleanField(
        "publié",
        default=False,
        help_text="Si activé, le protocole est visible par les répondants.",
    )
    # Identifiant du dispositif DSF correspondant (nullable : protocoles créés dans Sylvasan).
    dsf_dispositif_id = models.IntegerField("identifiant DSF dispositif", null=True, blank=True)
    # Champs saisis une fois par session, avant tout niveau hiérarchique (date, opérateur…).
    json_schema = models.JSONField("schéma JSON racine", null=True, blank=True)

    @property
    def response_data_schema(self):
        """Génère un SurveySchema compatible à partir de la hiérarchie de niveaux,
        utilisé pour l'affichage en lecture seule des sessions placettes.
        Charge tous les niveaux en une seule requête pour éviter les N+1."""
        children_by_parent: dict = {}
        for level in self.levels.filter(is_active=True).order_by("order"):
            children_by_parent.setdefault(level.parent_level_id, []).append(level)

        all_fields = []
        if self.json_schema:
            all_fields.extend(self.json_schema.get("fields", []))
        for root_level in children_by_parent.get(None, []):
            all_fields.extend(_level_to_fields(root_level, children_by_parent))
        return {"version": "1.0", "fields": all_fields}

    def __str__(self):
        return self.name
