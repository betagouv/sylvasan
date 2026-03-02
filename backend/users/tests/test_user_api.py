from common.utils import authenticate
from django.contrib.auth import get_user_model
from django.urls import reverse
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
