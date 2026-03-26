from django.db import models

from common.behaviours import Deactivable, Historisable, TimeStampable
from organisations.models import Organisation, Pole


class Campaign(TimeStampable, Deactivable, Historisable):
    class Meta:
        verbose_name = "campagne"

    title = models.CharField("titre")

    start_date = models.DateTimeField(verbose_name="date de début", null=True, blank=True)
    end_date = models.DateTimeField(verbose_name="date de fin", null=True, blank=True)

    organisation = models.ForeignKey(Organisation, related_name="campaigns", on_delete=models.CASCADE)
    pole = models.ForeignKey(Pole, related_name="campaigns", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
