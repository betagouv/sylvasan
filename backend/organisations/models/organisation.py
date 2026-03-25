from django.db import models

from common.behaviours import Deactivable, TimeStampable


class Organisation(TimeStampable, Deactivable):
    name = models.CharField("nom")
