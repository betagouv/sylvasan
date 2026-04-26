from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections

import bcrypt
from users.models import UserSource

User = get_user_model()


class DsfpAuthBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if "dsf_ref" not in settings.DATABASES:
            return None

        if not username or not password:
            return None

        with connections["dsf_ref"].cursor() as cursor:
            cursor.execute(
                """
                SELECT c.compte, c.passwd_hash, c.compte_actif, i.email1_ind, i.nom, i.prenom
                FROM dsfp.comptes c
                JOIN dsfp.individus i ON i.id_individu = c.id_individu
                WHERE c.compte = %s
                """,
                [username],
            )
            row = cursor.fetchone()

        if not row:
            return None

        compte, passwd_hash, actif, email, nom, prenom = row

        if not actif:
            return None

        try:
            if not bcrypt.checkpw(password.encode("utf-8"), passwd_hash.encode("utf-8")):
                return None
        except Exception:
            return None

        user, created = User.objects.get_or_create(
            username=compte,
            defaults={
                "email": email or "",
                "first_name": prenom or "",
                "last_name": nom or "",
                "source": UserSource.DSF,
                "external_id": compte,
            },
        )

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
