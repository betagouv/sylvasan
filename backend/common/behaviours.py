from django.db import models

from simple_history.models import HistoricalRecords


class TimeStampable(models.Model):
    class Meta:
        abstract = True

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)


class Deactivable(models.Model):
    class Meta:
        abstract = True

    is_active = models.BooleanField(default=True)


class Historisable(models.Model):
    class Meta:
        abstract = True

    history = HistoricalRecords(inherit=True)
