from django.db import models

from common.behaviours import Deactivable, TimeStampable


class Organisation(TimeStampable, Deactivable):
    name = models.CharField("nom")

    def __str__(self):
        return self.name
