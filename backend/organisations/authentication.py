import hashlib

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from organisations.models import ApiKey

_PREFIX = "Api-Key "


class ApiKeyAuthentication(BaseAuthentication):
    """
    Authentifie les requêtes portant un header `Authorization: Api-Key <key>`.

    Retourne (AnonymousUser, api_key_instance) en cas de succès.
    Retourne None si le schéma d'authentification n'est pas présent
    (la requête sera traitée par les autres classes d'authentification).
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(_PREFIX):
            return None

        raw_key = auth_header[len(_PREFIX) :]
        if "." not in raw_key:
            raise AuthenticationFailed("Format de clé API invalide.")

        prefix = raw_key.split(".", 1)[0]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        try:
            api_key = ApiKey.objects.select_related("organisation").get(
                prefix=prefix,
                hashed_key=key_hash,
                is_active=True,
            )
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed("Clé API invalide ou révoquée.")

        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("Clé API expirée.")

        return (AnonymousUser(), api_key)

    def authenticate_header(self, request):
        return _PREFIX.strip()
