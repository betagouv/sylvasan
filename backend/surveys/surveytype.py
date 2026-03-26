from django.db import models


# Les organisations peuvent décider d'ajouter des types d'enquêtes. Ces types
# doivent être répertoriées ici et implémentés sous leurs espaces sous
# organisation_specific
class SurveyType(models.TextChoices):
    SELF_CONTAINED = "self-contained", "Enquête générale"
