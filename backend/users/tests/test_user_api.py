from django.contrib.auth import get_user_model
from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory
from rest_framework import status
from rest_framework.test import APITestCase

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
        self.assertEqual(membership_data["organisation"], membership.organisation.id)
        self.assertIsNone(membership_data["pole"])
        self.assertEqual(membership_data["membershipType"], membership.membership_type)
