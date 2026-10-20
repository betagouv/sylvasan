import logging
import secrets
from typing import ClassVar

from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect

from authlib.integrations.django_client import OAuth
from organisations.models import Membership, Organisation, Pole
from organisations.models.membership import MembershipType
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, UserSource

logger = logging.getLogger(__name__)

oauth = OAuth()
oauth.register(
    name="portail",
    client_id=settings.DSF_OAUTH2_CLIENT_ID,
    client_secret=settings.DSF_OAUTH2_CLIENT_SECRET,
    server_metadata_url=f"{settings.DSF_OAUTH2_PORTAIL_URL}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid",
        "token_endpoint_auth_method": "client_secret_post",
    },
)


class DsfOAuthAppCallbackView(APIView):
    permission_classes: ClassVar[list] = []

    def post(self, request):
        code = request.data.get("code")
        nonce = request.data.get("nonce")
        redirect_uri = settings.DSF_OAUTH2_REDIRECT_APP_URI

        logger.info(
            "App OAuth callback received — code_present=%s nonce_present=%s",
            bool(code),
            bool(nonce),
        )

        if not code or not nonce:
            logger.error(
                "App OAuth failed: missing parameters — code_present=%s nonce_present=%s", bool(code), bool(nonce)
            )
            return Response({"error": "Code ou nonce manquant"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = oauth.portail.fetch_access_token(redirect_uri=redirect_uri, code=code)
            logger.info("App OAuth token exchange successful — token_type=%s", token.get("token_type"))
            claims = oauth.portail.parse_id_token(token, nonce=nonce)
            logger.info(
                "App OAuth claims parsed — sub=%s user_info=%s codes_da=%s",
                claims.get("sub"),
                claims.get("user_info"),
                claims.get("codes_da"),
            )
        except Exception:
            logger.exception("App OAuth token exchange failed")
            return Response({"error": "Échec OAuth2"}, status=status.HTTP_401_UNAUTHORIZED)

        if not claims.get("sub"):
            logger.error("App OAuth failed: sub missing in claims — full_claims=%s", claims)
            return Response({"error": "Identifiant manquant dans le token DSF"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user, echelon = _upsert_user_from_claims(claims)
        except Exception:
            logger.exception("App OAuth user upsert failed — sub=%s", claims.get("sub"))
            return Response(
                {"error": "Erreur lors de la création ou mise à jour de l'utilisateur"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(
            "App OAuth success — user_id=%s username=%s email=%s echelon=%s",
            user.id,
            user.username,
            user.email,
            echelon,
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "dsf_echelon": echelon,
                },
            }
        )


class DsfOAuthWebCallbackView(APIView):
    permission_classes: ClassVar[list] = []

    def get(self, request):
        state = request.query_params.get("state")
        logger.info("Web OAuth callback received — state_present=%s", bool(state))

        if not state or state != request.session.get("oauth_state"):
            logger.error("Web OAuth failed: state mismatch — returned_state=%s", state)
            return redirect(f"{settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT}/s-identifier?error=invalid_state")
        request.session.pop("oauth_state", None)

        code = request.query_params.get("code")
        nonce = request.session.get("oauth_nonce")

        logger.info("Web OAuth state validated — code_present=%s nonce_present=%s", bool(code), bool(nonce))

        if not code or not nonce:
            logger.error(
                "Web OAuth failed: missing parameters — code_present=%s nonce_present=%s", bool(code), bool(nonce)
            )
            return redirect(f"{settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT}/s-identifier?error=missing_params")

        try:
            token = oauth.portail.fetch_access_token(redirect_uri=settings.DSF_OAUTH2_REDIRECT_WEB_URI, code=code)
            logger.info("Web OAuth token exchange successful — token_type=%s", token.get("token_type"))
            claims = oauth.portail.parse_id_token(token, nonce=nonce)
            logger.info(
                "Web OAuth claims parsed — sub=%s user_info=%s codes_da=%s",
                claims.get("sub"),
                claims.get("user_info"),
                claims.get("codes_da"),
            )
        except Exception:
            logger.exception("Web OAuth token exchange failed")
            return redirect(f"{settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT}/s-identifier?error=oauth_failed")

        if not claims.get("sub"):
            logger.error("Web OAuth failed: sub missing in claims — full_claims=%s", claims)
            return redirect(f"{settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT}/s-identifier?error=missing_sub")

        try:
            user, _ = _upsert_user_from_claims(claims)
        except Exception:
            logger.exception("Web OAuth user upsert failed — sub=%s", claims.get("sub"))
            return redirect(f"{settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT}/s-identifier?error=upsert_failed")

        logger.info(
            "Web OAuth success — user_id=%s username=%s email=%s",
            user.id,
            user.username,
            user.email,
        )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.pop("oauth_nonce", None)

        return redirect(settings.DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT)


class DsfOAuthWebLoginView(APIView):
    permission_classes: ClassVar[list] = []

    def get(self, request):
        logger.info("Web OAuth login initiated — user=%s", request.user)

        nonce = secrets.token_urlsafe(16)
        request.session["oauth_nonce"] = nonce

        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state

        auth_url = oauth.portail.create_authorization_url(
            redirect_uri=settings.DSF_OAUTH2_REDIRECT_WEB_URI,
            nonce=nonce,
            state=state,
        )

        logger.info("Web OAuth redirecting to authorization URL")
        return redirect(auth_url["url"])


def _upsert_user_from_claims(claims: dict) -> tuple:
    # Le serveur DSF peut retourner des valeurs avec des espaces superflus — on normalise
    external_id = claims["sub"].strip()
    user_info = claims.get("user_info", {})
    codes_da = [str(c).strip() for c in claims.get("codes_da", [])]
    echelon = user_info.get("echelon", "").strip()
    email = user_info.get("email", "").strip()

    logger.info(
        "Upserting DSF user — sub=%s email=%s prenom=%s nom=%s echelon=%s codes_da=%s",
        external_id,
        email,
        user_info.get("prenom"),
        user_info.get("nom"),
        echelon,
        codes_da,
    )

    # Lookup priority:
    # 1) DSF user with this external_id (returning user)
    # 2) Any existing user with this email (first DSF login — link local account to DSF identity)
    user = User.objects.filter(external_id=external_id, source=UserSource.DSF).first()
    if user is None and email:
        user = User.objects.filter(email=email).first()
        if user:
            logger.info(
                "Linking existing user to DSF identity — user_id=%s username=%s email=%s sub=%s",
                user.id,
                user.username,
                email,
                external_id,
            )

    dsf_fields = {
        "external_id": external_id,
        "source": UserSource.DSF,
        "username": external_id,
        "email": email,
        "first_name": user_info.get("prenom", ""),
        "last_name": user_info.get("nom", ""),
        "dsf_last_claims": claims,
    }

    if user is not None:
        for field, value in dsf_fields.items():
            setattr(user, field, value)
        user.save()
        created = False
    else:
        user = User.objects.create(**dsf_fields)
        created = True

    logger.info(
        "DSF user %s — user_id=%s username=%s",
        "created" if created else "updated",
        user.id,
        user.username,
    )

    try:
        dsf = Organisation.objects.get(name="DSF")
        _assign_membership(user, dsf, echelon, codes_da)
    except Organisation.DoesNotExist:
        logger.warning("Organisation DSF not found, skipping membership assignment for user_id=%s", user.id)

    return user, echelon


def _assign_membership(user: User, organisation: Organisation, echelon: str, codes_da: list[str]):
    codes = set(codes_da)

    roles_to_assign = []

    if codes & {"SYLV-CREECAMPNAT-T", "SYLV-CREECAMPECH-T"}:
        pole_scoped = "SYLV-CREECAMPNAT-T" not in codes
        roles_to_assign.append((MembershipType.ADMIN, pole_scoped))

    if codes & {"SYLV-EDIT-T", "SYLV-EDIT_ECH-T"}:
        pole_scoped = "SYLV-EDIT-T" not in codes
        roles_to_assign.append((MembershipType.RESPONDER, pole_scoped))

    logger.info(
        "Assigning memberships — user_id=%s username=%s echelon=%s codes_da=%s roles_to_assign=%s",
        user.id,
        user.username,
        echelon,
        codes_da,
        [(r[0], "pole_scoped" if r[1] else "national") for r in roles_to_assign],
    )

    if not roles_to_assign:
        deleted, _ = Membership.objects.filter(user=user, organisation=organisation).delete()
        logger.info("No matching roles — deleted %s existing membership(s) for user_id=%s", deleted, user.id)
        return

    pole = None
    if echelon:
        pole = Pole.objects.filter(organisation=organisation, dsf_code=echelon, is_active=True).first()
        logger.info("Pole lookup — echelon=%s found=%s pole_id=%s", echelon, bool(pole), pole.id if pole else None)

    # active_keys : ensemble des (type, pole_id) à conserver après la boucle
    active_keys: set[tuple] = set()
    for membership_type, is_pole_scoped in roles_to_assign:
        if is_pole_scoped and not pole:
            logger.warning(
                "Pole with dsf_code='%s' not found for user_id=%s username=%s — "
                "skipping pole-scoped %s membership. Run sync_dsf_poles to fix this.",
                echelon,
                user.id,
                user.username,
                membership_type,
            )
            continue

        assigned_pole = pole if is_pole_scoped else None
        # Utiliser get_or_create avec la clé unique complète (type + pôle) pour éviter
        # MultipleObjectsReturned si des doublons existent en base
        _, created = Membership.objects.get_or_create(
            user=user,
            organisation=organisation,
            membership_type=membership_type,
            pole=assigned_pole,
        )
        logger.info(
            "Membership %s — user_id=%s username=%s type=%s pole=%s",
            "created" if created else "existing",
            user.id,
            user.username,
            membership_type,
            assigned_pole,
        )
        active_keys.add((membership_type, assigned_pole.id if assigned_pole else None))

    # Supprimer les memberships dont le type n'est plus actif
    deleted_total = 0
    deleted, _ = (
        Membership.objects.filter(user=user, organisation=organisation)
        .exclude(membership_type__in={k[0] for k in active_keys})
        .delete()
    )
    deleted_total += deleted

    # Supprimer les memberships du bon type mais avec un pôle devenu obsolète
    for membership_type, pole_id in active_keys:
        qs = Membership.objects.filter(user=user, organisation=organisation, membership_type=membership_type)
        deleted, _ = (qs.filter(pole__isnull=False) if pole_id is None else qs.exclude(pole_id=pole_id)).delete()
        deleted_total += deleted

    if deleted_total:
        logger.info("Removed %s stale membership(s) for user_id=%s username=%s", deleted_total, user.id, user.username)
