from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from users.factories import UserFactory

LOGIN_URL = reverse("login")
MOBILE_TOKEN_URL = reverse("mobile_token")


class TestLoginView(APITestCase):
    def test_inactive_account_correct_password_returns_403(self):
        """
        Un compte non activé avec le bon mot de passe doit retourner un 403
        avec le code 'account_not_activated', et non un 401 générique.
        """
        password = "Sylva$an2024!"
        user = UserFactory(is_active=False, password=password)

        response = self.client.post(
            LOGIN_URL,
            {"username": user.username, "password": password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get("error"), "account_not_activated")

    def test_inactive_account_wrong_password_returns_401(self):
        """
        Un compte non activé avec un mauvais mot de passe doit retourner
        un 401 normal, sans révéler l'état du compte.
        """
        user = UserFactory(is_active=False, password="bon_mot_de_passe")

        response = self.client.post(
            LOGIN_URL,
            {"username": user.username, "password": "mauvais_mot_de_passe"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_active_account_correct_password_returns_200(self):
        """
        Un compte actif avec les bons identifiants doit retourner un 200.
        """
        password = "Sylva$an2024!"
        user = UserFactory(is_active=True, password=password)

        response = self.client.post(
            LOGIN_URL,
            {"username": user.username, "password": password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.json())


class TestMobileTokenView(APITestCase):
    def test_login_avec_username_retourne_tokens(self):
        """
        L'endpoint mobile accepte un nom d'utilisateur et retourne access + refresh.
        """
        password = "Sylva$an2024!"
        user = UserFactory(password=password)

        response = self.client.post(
            MOBILE_TOKEN_URL,
            {"username": user.username, "password": password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_login_avec_email_retourne_tokens(self):
        """
        L'endpoint mobile accepte une adresse email à la place du nom d'utilisateur.
        """
        password = "Sylva$an2024!"
        user = UserFactory(password=password)

        response = self.client.post(
            MOBILE_TOKEN_URL,
            {"username": user.email, "password": password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_login_email_mauvais_mot_de_passe_retourne_401(self):
        """
        Un email valide avec un mauvais mot de passe retourne 401.
        """
        user = UserFactory(password="bon_mot_de_passe")

        response = self.client.post(
            MOBILE_TOKEN_URL,
            {"username": user.email, "password": "mauvais"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_inconnu_retourne_401(self):
        """
        Un email qui ne correspond à aucun compte retourne 401.
        """
        response = self.client.post(
            MOBILE_TOKEN_URL,
            {"username": "inconnu@example.com", "password": "motdepasse"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
