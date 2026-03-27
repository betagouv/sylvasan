from django.contrib.auth import get_user_model
from django.db import models

from common.behaviours import TimeStampable

from .organisation import Organisation
from .pole import Pole


class MembershipType(models.TextChoices):
    ADMIN = "admin", "Administrateur"
    MANAGER = "manager", "Responsable"
    RESPONDER = "responder", "Répondant"


class Membership(TimeStampable):
    # TODO : unique constraint on org/pole/user ?
    class Meta:
        verbose_name = "rôle"

    user = models.ForeignKey(
        get_user_model(),
        related_name="memberships",
        verbose_name="Utilisateur ou utilisatrice",
        on_delete=models.CASCADE,
    )
    organisation = models.ForeignKey(Organisation, related_name="memberships", on_delete=models.CASCADE)

    # Si besoin de restreindre le rôle à un pôle de l'organisation cette colonne doit être remplie
    pole = models.ForeignKey(Pole, related_name="memberships", null=True, blank=True, on_delete=models.CASCADE)
    membership_type = models.CharField(choices=MembershipType, verbose_name="type de rôle")

    def __str__(self):
        return f"{self.user} – {self.organisation} ({self.membership_type})"
