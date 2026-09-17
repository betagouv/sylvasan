import hashlib
import secrets

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.behaviours import TimeStampable

from .organisation import Organisation


class ApiKey(TimeStampable):
    name = models.CharField(_("nom"), max_length=100)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name=_("organisation"),
    )
    prefix = models.CharField(max_length=8, unique=True, editable=False)
    hashed_key = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(_("date d'expiration"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("clé API")
        verbose_name_plural = _("clés API")

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @staticmethod
    def generate() -> tuple[str, str, str]:
        """Génère une clé et retourne (raw_key, prefix, hashed_key).

        Format : {prefix}.{secret} — le préfixe est stocké en clair
        pour permettre une recherche rapide ; seul le hash SHA-256 de
        la clé complète est persisté.
        """
        prefix = secrets.token_urlsafe(6)  # 8 chars base64url
        secret = secrets.token_urlsafe(32)  # 43 chars base64url
        raw_key = f"{prefix}.{secret}"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, prefix, hashed_key
