import datetime
import itertools

from django.urls import reverse
from django.utils import timezone

from responses.factories import ResponseFactory
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from users.factories import UserFactory


class TestStatsEndpoint(APITestCase):
    def test_endpoint_accessible_without_authentication(self):
        """
        L'endpoint /api/stats/ est accessible sans authentification.
        """
        response = self.client.get(reverse("stats"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_three_stats(self):
        """
        L'endpoint retourne exactement trois statistiques : comptes, enquêtes, observations.
        """
        response = self.client.get(reverse("stats"), format="json")
        data = response.json()
        self.assertEqual(len(data), 3)
        ids = [s["id"] for s in data]
        self.assertEqual(ids, ["active-users", "active-surveys", "active-responses"])

    def test_each_stat_has_required_fields(self):
        """
        Chaque statistique contient les champs id, type, title, description et data.
        """
        response = self.client.get(reverse("stats"), format="json")
        for stat in response.json():
            self.assertIn("id", stat)
            self.assertIn("type", stat)
            self.assertIn("title", stat)
            self.assertIn("description", stat)
            self.assertIn("data", stat)
            self.assertIn("labels", stat["data"])
            self.assertIn("datasets", stat["data"])

    def test_active_users_counted(self):
        """
        Les comptes actifs sont comptabilisés dans la stat active-users.
        """
        UserFactory.create_batch(3)
        response = self.client.get(reverse("stats"), format="json")
        active_users_stat = next(s for s in response.json() if s["id"] == "active-users")
        total = sum(active_users_stat["data"]["datasets"][0]["data"])
        self.assertEqual(total, 3)

    def test_inactive_users_excluded(self):
        """
        Les comptes désactivés (is_active=False) ne sont pas comptabilisés.
        """
        UserFactory.create_batch(2)
        inactive = UserFactory.create()
        inactive.deactivate()

        response = self.client.get(reverse("stats"), format="json")
        active_users_stat = next(s for s in response.json() if s["id"] == "active-users")
        total = sum(active_users_stat["data"]["datasets"][0]["data"])
        self.assertEqual(total, 2)

    def test_active_surveys_counted(self):
        """
        Les enquêtes actives sont comptabilisées dans la stat active-surveys.
        """
        SurveyFactory.create_batch(2)
        response = self.client.get(reverse("stats"), format="json")
        surveys_stat = next(s for s in response.json() if s["id"] == "active-surveys")
        total = sum(surveys_stat["data"]["datasets"][0]["data"])
        self.assertEqual(total, 2)

    def test_inactive_surveys_excluded(self):
        """
        Les enquêtes désactivées (is_active=False) ne sont pas comptabilisées.
        """
        SurveyFactory.create_batch(2)
        inactive = SurveyFactory.create()
        inactive.deactivate()

        response = self.client.get(reverse("stats"), format="json")
        surveys_stat = next(s for s in response.json() if s["id"] == "active-surveys")
        total = sum(surveys_stat["data"]["datasets"][0]["data"])
        self.assertEqual(total, 2)

    def test_active_responses_counted(self):
        """
        Les observations actives sont comptabilisées dans la stat active-responses.
        """
        ResponseFactory.create_batch(4)
        response = self.client.get(reverse("stats"), format="json")
        responses_stat = next(s for s in response.json() if s["id"] == "active-responses")
        total = sum(responses_stat["data"]["datasets"][0]["data"])
        self.assertEqual(total, 4)

    def test_cumulative_counts_are_monotonically_increasing(self):
        """
        Les données cumulatives sont toujours croissantes ou stables d'un mois à l'autre.
        """
        now = timezone.now()
        for i in range(3):
            u = UserFactory.create()
            u.creation_date = now - datetime.timedelta(days=30 * i)
            u.save()

        response = self.client.get(reverse("stats"), format="json")
        data = next(s for s in response.json() if s["id"] == "active-users")["data"]["datasets"][0]["data"]
        for prev, curr in itertools.pairwise(data):
            self.assertGreaterEqual(curr, prev)

    def test_labels_and_data_have_same_length(self):
        """
        Les labels et les données ont la même longueur pour chaque statistique.
        """
        UserFactory.create_batch(2)
        SurveyFactory.create_batch(2)
        ResponseFactory.create_batch(2)

        response = self.client.get(reverse("stats"), format="json")
        for stat in response.json():
            labels = stat["data"]["labels"]
            data = stat["data"]["datasets"][0]["data"]
            self.assertEqual(len(labels), len(data), f"Mismatch for stat '{stat['id']}'")

    def test_empty_stat_returns_empty_arrays(self):
        """
        Sans données en base, les tableaux labels et data sont vides.
        """
        response = self.client.get(reverse("stats"), format="json")
        for stat in response.json():
            self.assertEqual(stat["data"]["labels"], [])
            self.assertEqual(stat["data"]["datasets"][0]["data"], [])
