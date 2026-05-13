import logging
import secrets

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
    permission_classes = []

    def post(self, request):
        code = request.data.get("code")
        nonce = request.data.get("nonce")
        redirect_uri = settings.DSF_OAUTH2_REDIRECT_URI

        if not code or not nonce:
            return Response({"error": "Code ou nonce manquant"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = oauth.portail.fetch_access_token(
                redirect_uri=redirect_uri,
                code=code,
            )
            claims = oauth.portail.parse_id_token(token, nonce=nonce)
        except Exception:
            logger.exception("DSF OAuth token exchange failed")
            return Response({"error": "Échec OAuth2"}, status=status.HTTP_401_UNAUTHORIZED)

        user, echelon, codes_da = _upsert_user_from_claims(claims)

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
    permission_classes = []

    def get(self, request):
        code = request.query_params.get("code")
        nonce = request.session.get("oauth_nonce")

        if not code or not nonce:
            return redirect(f"{settings.FRONTEND_URL}/login?error=missing_params")

        try:
            token = oauth.portail.fetch_access_token(
                redirect_uri=settings.DSF_OAUTH2_WEB_REDIRECT_URI,
                code=code,
            )
            claims = oauth.portail.parse_id_token(token, nonce=nonce)
        except Exception:
            logger.exception("DSF OAuth web callback failed")
            return redirect(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

        user, echelon, codes_da = _upsert_user_from_claims(claims)

        # Création de la session Django
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.pop("oauth_nonce", None)

        return redirect("/")


class DsfOAuthWebLoginView(APIView):
    permission_classes = []

    def get(self, request):
        nonce = secrets.token_urlsafe(16)
        request.session["oauth_nonce"] = nonce

        auth_url = oauth.portail.create_authorization_url(
            settings.DSF_OAUTH2_AUTHORIZATION_URL,
            redirect_uri=settings.DSF_OAUTH2_WEB_REDIRECT_URI,
            nonce=nonce,
        )

        return redirect(auth_url[0])


def _upsert_user_from_claims(claims: dict):

    external_id = claims.get("sub")
    if not external_id:
        raise ValueError("Identifiant manquant dans le token DSF")

    external_id = claims.get("sub")
    user_info = claims.get("user_info", {})
    codes_da = claims.get("codes_da", [])
    echelon = user_info.get("echelon", "")

    user, _ = User.objects.update_or_create(
        external_id=external_id,
        source=UserSource.DSF,
        defaults={
            "username": external_id,
            "email": user_info.get("email", ""),
            "first_name": user_info.get("prenom", ""),
            "last_name": user_info.get("nom", ""),
        },
    )

    try:
        dsf = Organisation.objects.get(name="DSF")
        _assign_membership(user, dsf, echelon, codes_da)
    except Organisation.DoesNotExist:
        pass

    return user, echelon, codes_da


def _assign_membership(user: User, organisation: Organisation, echelon: str, codes_da: list[str]):
    codes = set(codes_da)

    roles_to_assign = []

    if codes & {"SYLV-CREECAMPNAT-T", "SYLV-CREECAMPECH-T"}:
        pole_scoped = "SYLV-CREECAMPNAT-T" not in codes
        roles_to_assign.append((MembershipType.ADMIN, pole_scoped))

    if codes & {"SYLV-EDIT-T", "SYLV-EDIT_ECH-T"}:
        pole_scoped = "SYLV-EDIT-T" not in codes
        roles_to_assign.append((MembershipType.RESPONDER, pole_scoped))

    if not roles_to_assign:
        Membership.objects.filter(user=user, organisation=organisation).delete()
        return

    pole = None
    if echelon:
        pole = Pole.objects.filter(
            organisation=organisation,
            dsf_code=echelon,
            is_active=True,
        ).first()

    active_types = set()
    for membership_type, is_pole_scoped in roles_to_assign:
        if is_pole_scoped and not pole:
            logger.warning(
                f"Pole with dsf_code='{echelon}' not found for user '{user.username}'. "
                f"Skipping pole-scoped {membership_type} membership. "
                f"Run sync_dsf_poles to fix this."
            )
            continue

        assigned_pole = pole if is_pole_scoped else None
        Membership.objects.update_or_create(
            user=user,
            organisation=organisation,
            membership_type=membership_type,
            defaults={"pole": assigned_pole},
        )
        active_types.add(membership_type)

    Membership.objects.filter(user=user, organisation=organisation).exclude(membership_type__in=active_types).delete()
