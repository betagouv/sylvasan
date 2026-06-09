from django.contrib.auth import get_user_model
from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import VocabularySetFactory

User = get_user_model()


class TestUserApi(APITestCase):
    def test_me_unauthenticated(self):
        """
        L'endpoint /me retourne un no-content si la personne n'est pas authentifiée
        """
        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_me_authenticated(self):
        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(json_response["id"], authenticate.user.id)
        self.assertEqual(json_response["firstName"], authenticate.user.first_name)
        self.assertEqual(json_response["lastName"], authenticate.user.last_name)
        self.assertEqual(json_response["username"], authenticate.user.username)
        self.assertEqual(json_response["memberships"], [])

    @authenticate
    def test_me_authenticated_returns_memberships(self):
        """
        L'endpoint /me retourne les rôles de l'utilisateur connecté
        """
        membership = MembershipFactory(user=authenticate.user)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response["memberships"]), 1)

        membership_data = json_response["memberships"][0]
        self.assertEqual(membership_data["organisation"]["id"], membership.organisation.id)
        self.assertEqual(membership_data["organisation"]["name"], membership.organisation.name)
        self.assertIsNone(membership_data["pole"])
        self.assertEqual(membership_data["membershipType"], membership.membership_type)

    @authenticate
    def test_me_returns_organisations_key(self):
        """
        L'endpoint /me inclut une clé 'organisations' même sans rôle
        """
        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("organisations", response.json())
        self.assertEqual(response.json()["organisations"], [])

    @authenticate
    def test_me_returns_organisations_with_poles(self):
        """
        L'endpoint /me retourne les organisations de l'utilisateur avec leurs pôles
        """
        org = OrganisationFactory()
        pole_a = PoleFactory(organisation=org)
        pole_b = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        organisations = response.json()["organisations"]
        self.assertEqual(len(organisations), 1)

        org_data = organisations[0]
        self.assertEqual(org_data["id"], org.id)
        self.assertEqual(org_data["name"], org.name)

        pole_ids = {p["id"] for p in org_data["poles"]}
        self.assertIn(pole_a.id, pole_ids)
        self.assertIn(pole_b.id, pole_ids)

    @authenticate
    def test_me_organisations_excludes_inactive_poles(self):
        """
        Les pôles inactifs ne sont pas inclus dans la liste des pôles d'une organisation
        """
        org = OrganisationFactory()
        active_pole = PoleFactory(organisation=org)
        inactive_pole = PoleFactory(organisation=org, is_active=False)
        MembershipFactory(user=authenticate.user, organisation=org)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pole_ids = {p["id"] for p in response.json()["organisations"][0]["poles"]}
        self.assertIn(active_pole.id, pole_ids)
        self.assertNotIn(inactive_pole.id, pole_ids)

    @authenticate
    def test_me_organisations_deduplicated_across_memberships(self):
        """
        Une organisation n'apparaît qu'une seule fois même si l'utilisateur
        a plusieurs rôles dans cette organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        organisations = response.json()["organisations"]
        self.assertEqual(len(organisations), 1)

    @authenticate
    def test_me_organisations_includes_all_user_orgs(self):
        """
        Toutes les organisations de l'utilisateur sont retournées
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org_a)
        MembershipFactory(user=authenticate.user, organisation=org_b)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        org_ids = {o["id"] for o in response.json()["organisations"]}
        self.assertIn(org_a.id, org_ids)
        self.assertIn(org_b.id, org_ids)


class TestUserApiVocabularies(APITestCase):
    @authenticate
    def test_me_returns_vocabularies_key(self):
        """
        L'endpoint /me inclut une clé 'vocabularies' même sans rôle ni vocabulaire
        """
        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("vocabularies", response.json())

    @authenticate
    def test_me_returns_shared_vocabularies_without_membership(self):
        """
        Un utilisateur sans rôle voit les vocabulaires partagés (organisation=None)
        """
        shared = VocabularySetFactory(organisation=None)
        VocabularySetFactory(organisation=OrganisationFactory())  # non partagé, non accessible

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        codes = {v["code"] for v in response.json()["vocabularies"]}
        self.assertIn(shared.code, codes)

    @authenticate
    def test_me_returns_org_vocabularies_for_member(self):
        """
        Un utilisateur avec un rôle dans une organisation voit les vocabulaires de cette organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org)
        org_vocab = VocabularySetFactory(organisation=org)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        codes = {v["code"] for v in response.json()["vocabularies"]}
        self.assertIn(org_vocab.code, codes)
        self.assertNotIn(other_vocab.code, codes)

    @authenticate
    def test_me_vocabularies_contain_only_display_fields(self):
        """
        Les vocabulaires retournés par /me ne contiennent que id, code et name —
        pas les entrées (représentation allégée, identique à l'endpoint /vocabularies/)
        """
        VocabularySetFactory(organisation=None)

        response = self.client.get(reverse("me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        vocab_data = response.json()["vocabularies"][0]
        self.assertIn("id", vocab_data)
        self.assertIn("code", vocab_data)
        self.assertIn("name", vocab_data)
        self.assertNotIn("entries", vocab_data)
