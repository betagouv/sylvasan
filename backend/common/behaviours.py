from django.db import models


class TimeStampable(models.Model):
    class Meta:
        abstract = True

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)


class Deactivable(models.Model):
    class Meta:
        abstract = True

    is_active = models.BooleanField(default=True)
