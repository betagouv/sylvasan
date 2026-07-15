from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import Membership
from organisations.models.membership import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from users.factories import UserFactory
from users.models import User, UserSource

from organisation_specific.dsf.views.oauth import _assign_membership, oauth

MOCK_CLAIMS = {
    "sub": "CO12345",
    "user_info": {
        "email": "agent@example.com",
        "prenom": "Jean",
        "nom": "Dupont",
        "echelon": "ECH001",
    },
    "codes_da": ["SYLV-EDIT-T"],
}

DSF_SETTINGS = dict(
    DSF_OAUTH2_REDIRECT_APP_URI="sylvasan://oauth/callback",
    DSF_OAUTH2_REDIRECT_WEB_URI="https://example.com/platform/dsf/oauth/web/callback/",
    DSF_OAUTH2_WEB_SUCCESS_REDIRECT_ROOT="https://example.com",
)


def _mock_oauth(claims=None):
    claims = claims if claims is not None else MOCK_CLAIMS
    return (
        patch.object(oauth.portail, "fetch_access_token", return_value={"id_token": "tok"}),
        patch.object(oauth.portail, "parse_id_token", return_value=claims),
    )


@override_settings(**DSF_SETTINGS)
class TestDsfOAuthAppCallback(APITestCase):
    URL = "dsf-oauth-app-callback"

    def test_missing_code_returns_400(self):
        response = self.client.post(reverse(self.URL), {"nonce": "abc"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_nonce_returns_400(self):
        response = self.client.post(reverse(self.URL), {"code": "abc"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_exchange_failure_returns_401(self):
        with patch.object(oauth.portail, "fetch_access_token", side_effect=Exception("network error")):
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_sub_returns_401(self):
        claims_without_sub = {**MOCK_CLAIMS, "sub": None}
        fetch_patch, parse_patch = _mock_oauth(claims_without_sub)
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creates_new_user_and_returns_tokens(self):
        fetch_patch, parse_patch = _mock_oauth()
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertTrue(User.objects.filter(external_id="CO12345", source=UserSource.DSF).exists())

    def test_updates_existing_user(self):
        UserFactory.create(external_id="CO12345", source=UserSource.DSF, username="CO12345")
        fetch_patch, parse_patch = _mock_oauth()
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(external_id="CO12345", source=UserSource.DSF).count(), 1)

    def test_sub_with_trailing_space_matches_existing_dsf_user(self):
        """
        Le serveur DSF peut retourner un sub avec des espaces superflus (ex : "CO12345 ").
        Le sub doit être normalisé avant la recherche pour retrouver l'utilisateur existant
        et ne pas créer de doublon ni lever une UniqueViolation sur l'email.
        """
        UserFactory.create(external_id="CO12345", source=UserSource.DSF, username="CO12345", email="agent@example.com")

        claims_with_space = {**MOCK_CLAIMS, "sub": "CO12345 "}  # espace après l'id
        fetch_patch, parse_patch = _mock_oauth(claims_with_space)
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(external_id="CO12345").count(), 1)

    def test_links_existing_local_account_by_email(self):
        """
        Si un compte local existe déjà avec le même email que celui retourné par DSF,
        le compte est mis à jour (source=DSF, external_id) au lieu d'en créer un nouveau.
        Cela évite la violation de contrainte unique sur l'email.
        """
        existing = UserFactory.create(email="agent@example.com", source=UserSource.LOCAL)
        original_id = existing.id

        fetch_patch, parse_patch = _mock_oauth()
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Aucun doublon créé
        self.assertEqual(User.objects.filter(email="agent@example.com").count(), 1)
        # C'est bien le compte existant qui a été mis à jour, pas un nouveau
        updated = User.objects.get(email="agent@example.com")
        self.assertEqual(updated.id, original_id)
        self.assertEqual(updated.external_id, "CO12345")

    def test_assigns_membership_on_login(self):
        OrganisationFactory.create(name="DSF")
        fetch_patch, parse_patch = _mock_oauth()
        with fetch_patch, parse_patch:
            self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        user = User.objects.get(external_id="CO12345")
        self.assertTrue(Membership.objects.filter(user=user, membership_type=MembershipType.RESPONDER).exists())

    def test_all_roles_with_nonexistent_echelon_returns_200_and_creates_national_memberships(self):
        """
        Quand le DSF retourne tous les codes et un échelon inconnu,
        l'authentification réussit (200) et les adhésions nationales sont créées sans pôle.
        """
        OrganisationFactory.create(name="DSF")
        claims = {
            "sub": "CO99999",
            "user_info": {
                "nom": "MARTIN",
                "email": "martin@example.com",
                "grade": None,
                "prenom": "Martin",
                "echelon": "NON_EXISTENT",
                "categorie": "E",
            },
            "codes_da": ["SYLV-CREECAMPNAT-T", "SYLV-CREECAMPECH-T", "SYLV-EDIT-T"],
        }
        fetch_patch, parse_patch = _mock_oauth(claims)
        with fetch_patch, parse_patch:
            response = self.client.post(reverse(self.URL), {"code": "c", "nonce": "n"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(external_id="CO99999")
        admin_m = Membership.objects.get(user=user, membership_type=MembershipType.ADMIN)
        responder_m = Membership.objects.get(user=user, membership_type=MembershipType.RESPONDER)
        self.assertIsNone(admin_m.pole)
        self.assertIsNone(responder_m.pole)


@override_settings(**DSF_SETTINGS)
class TestDsfOAuthWebLogin(APITestCase):
    URL = "dsf-oauth-web-login"

    def test_stores_nonce_and_state_in_session(self):
        with patch.object(
            oauth.portail,
            "create_authorization_url",
            return_value={"url": "https://dsf.example/auth"},
        ):
            self.client.get(reverse(self.URL))

        session = self.client.session
        self.assertIn("oauth_nonce", session)
        self.assertIn("oauth_state", session)

    def test_redirects_to_authorization_url(self):
        auth_url = "https://dsf.example/auth?response_type=code"
        with patch.object(
            oauth.portail,
            "create_authorization_url",
            return_value={"url": auth_url},
        ):
            response = self.client.get(reverse(self.URL))

        self.assertRedirects(response, auth_url, fetch_redirect_response=False)


@override_settings(**DSF_SETTINGS)
class TestDsfOAuthWebCallback(APITestCase):
    URL = "dsf-oauth-web-callback"

    def _set_session(self, state=None, nonce=None):
        session = self.client.session
        if state is not None:
            session["oauth_state"] = state
        if nonce is not None:
            session["oauth_nonce"] = nonce
        session.save()

    def test_missing_state_redirects_to_error(self):
        response = self.client.get(reverse(self.URL), {"code": "c"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=invalid_state",
            fetch_redirect_response=False,
        )

    def test_state_mismatch_redirects_to_error(self):
        self._set_session(state="correct_state")
        response = self.client.get(reverse(self.URL), {"code": "c", "state": "wrong_state"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=invalid_state",
            fetch_redirect_response=False,
        )

    def test_missing_code_redirects_to_error(self):
        self._set_session(state="s", nonce="n")
        response = self.client.get(reverse(self.URL), {"state": "s"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=missing_params",
            fetch_redirect_response=False,
        )

    def test_missing_nonce_in_session_redirects_to_error(self):
        self._set_session(state="s")
        response = self.client.get(reverse(self.URL), {"code": "c", "state": "s"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=missing_params",
            fetch_redirect_response=False,
        )

    def test_token_exchange_failure_redirects_to_error(self):
        self._set_session(state="s", nonce="n")
        with patch.object(oauth.portail, "fetch_access_token", side_effect=Exception("err")):
            response = self.client.get(reverse(self.URL), {"code": "c", "state": "s"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=oauth_failed",
            fetch_redirect_response=False,
        )

    def test_missing_sub_redirects_to_error(self):
        self._set_session(state="s", nonce="n")
        fetch_patch, parse_patch = _mock_oauth({**MOCK_CLAIMS, "sub": None})
        with fetch_patch, parse_patch:
            response = self.client.get(reverse(self.URL), {"code": "c", "state": "s"})
        self.assertRedirects(
            response,
            "https://example.com/s-identifier?error=missing_sub",
            fetch_redirect_response=False,
        )

    def test_successful_login_creates_session_and_redirects(self):
        self._set_session(state="s", nonce="n")
        fetch_patch, parse_patch = _mock_oauth()
        with fetch_patch, parse_patch:
            response = self.client.get(reverse(self.URL), {"code": "c", "state": "s"})

        self.assertRedirects(response, "https://example.com", fetch_redirect_response=False)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        session = self.client.session
        self.assertNotIn("oauth_nonce", session)
        self.assertNotIn("oauth_state", session)


class TestAssignMembership(APITestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.org = OrganisationFactory.create(name="DSF")

    def test_no_codes_deletes_all_memberships(self):
        MembershipFactory.create(user=self.user, organisation=self.org)
        _assign_membership(self.user, self.org, "", [])
        self.assertEqual(Membership.objects.filter(user=self.user, organisation=self.org).count(), 0)

    def test_national_admin_creates_membership_without_pole(self):
        _assign_membership(self.user, self.org, "", ["SYLV-CREECAMPNAT-T"])
        m = Membership.objects.get(user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN)
        self.assertIsNone(m.pole)

    def test_scoped_admin_creates_membership_with_pole(self):
        pole = PoleFactory.create(organisation=self.org, dsf_code="ECH001")
        _assign_membership(self.user, self.org, "ECH001", ["SYLV-CREECAMPECH-T"])
        m = Membership.objects.get(user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN)
        self.assertEqual(m.pole, pole)

    def test_national_responder_creates_membership_without_pole(self):
        _assign_membership(self.user, self.org, "", ["SYLV-EDIT-T"])
        m = Membership.objects.get(user=self.user, organisation=self.org, membership_type=MembershipType.RESPONDER)
        self.assertIsNone(m.pole)

    def test_scoped_responder_creates_membership_with_pole(self):
        pole = PoleFactory.create(organisation=self.org, dsf_code="ECH001")
        _assign_membership(self.user, self.org, "ECH001", ["SYLV-EDIT_ECH-T"])
        m = Membership.objects.get(user=self.user, organisation=self.org, membership_type=MembershipType.RESPONDER)
        self.assertEqual(m.pole, pole)

    def test_missing_pole_skips_scoped_role(self):
        _assign_membership(self.user, self.org, "ECH001", ["SYLV-CREECAMPECH-T"])
        self.assertEqual(Membership.objects.filter(user=self.user, organisation=self.org).count(), 0)

    def test_all_roles_with_nonexistent_echelon_creates_national_memberships(self):
        """
        Quand tous les codes sont présents et que l'échelon ne correspond à aucun pôle,
        les codes nationaux (SYLV-CREECAMPNAT-T, SYLV-EDIT-T) ont la priorité :
        les adhésions ADMIN et RESPONDER sont créées sans pôle.
        """
        _assign_membership(
            self.user,
            self.org,
            "NON_EXISTENT",
            ["SYLV-CREECAMPNAT-T", "SYLV-CREECAMPECH-T", "SYLV-EDIT-T"],
        )
        admin_m = Membership.objects.get(user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN)
        responder_m = Membership.objects.get(
            user=self.user, organisation=self.org, membership_type=MembershipType.RESPONDER
        )
        self.assertIsNone(admin_m.pole)
        self.assertIsNone(responder_m.pole)

    def test_stale_role_removed(self):
        MembershipFactory.create(user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN)
        _assign_membership(self.user, self.org, "", ["SYLV-EDIT-T"])
        self.assertFalse(
            Membership.objects.filter(
                user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN
            ).exists()
        )
        self.assertTrue(
            Membership.objects.filter(
                user=self.user, organisation=self.org, membership_type=MembershipType.RESPONDER
            ).exists()
        )

    def test_no_codes_does_not_delete_other_org_memberships(self):
        """
        Quand aucun code DSF n'est présent et que les adhésions DSF sont supprimées,
        les adhésions d'autres organisations ne doivent pas être touchées.
        """
        other_org = OrganisationFactory.create(name="Foo")
        other_membership = MembershipFactory.create(user=self.user, organisation=other_org)
        MembershipFactory.create(user=self.user, organisation=self.org)

        _assign_membership(self.user, self.org, "", [])

        self.assertEqual(Membership.objects.filter(user=self.user, organisation=self.org).count(), 0)
        self.assertTrue(Membership.objects.filter(pk=other_membership.pk).exists())

    def test_assigning_roles_does_not_touch_other_org_memberships(self):
        """
        L'attribution de rôles DSF ne doit pas modifier les adhésions d'autres organisations.
        """
        other_org = OrganisationFactory.create(name="Foo")
        other_membership = MembershipFactory.create(user=self.user, organisation=other_org)

        _assign_membership(self.user, self.org, "", ["SYLV-EDIT-T"])

        self.assertTrue(Membership.objects.filter(pk=other_membership.pk).exists())

    def test_stale_role_removal_does_not_touch_other_org_memberships(self):
        """
        La suppression des rôles DSF obsolètes ne doit pas affecter les adhésions d'autres organisations.
        """
        other_org = OrganisationFactory.create(name="Foo")
        other_membership = MembershipFactory.create(user=self.user, organisation=other_org)
        MembershipFactory.create(user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN)

        _assign_membership(self.user, self.org, "", ["SYLV-EDIT-T"])

        self.assertFalse(
            Membership.objects.filter(
                user=self.user, organisation=self.org, membership_type=MembershipType.ADMIN
            ).exists()
        )
        self.assertTrue(Membership.objects.filter(pk=other_membership.pk).exists())
