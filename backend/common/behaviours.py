from django.db import models

from simple_history.models import HistoricalRecords


class TimeStampable(models.Model):
    class Meta:
        abstract = True

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)


class DeactivableQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Deactivable(models.Model):
    class Meta:
        abstract = True

    is_active = models.BooleanField(default=True)

    def activate(self):
        self.is_active = True
        self.save()

    def deactivate(self):
        self.is_active = False
        self.save()

    @property
    def activity_icon(self):
        return "✅" if self.is_active else "❌"

    activity_icon.fget.short_description = "Actif ?"


class Historisable(models.Model):
    class Meta:
        abstract = True

    history = HistoricalRecords(inherit=True)
