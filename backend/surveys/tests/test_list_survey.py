from django.urls import reverse
from django.utils import timezone

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory


class TestListSurvey(APITestCase):
    def test_unauthenticated_cannot_list_surveys(self):
        """
        Un utilisateur non authentifié ne peut pas lister les enquêtes
        """
        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_returns_empty_list(self):
        """
        Un utilisateur sans rôle ne voit aucune enquête
        """
        SurveyFactory()
        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["results"], [])

    @authenticate
    def test_org_member_sees_org_surveys(self):
        """
        Un membre d'organisation voit les enquêtes au niveau de l'organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(reverse("survey_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], survey.id)

    @authenticate
    def test_org_member_sees_pole_surveys_within_org(self):
        """
        Un membre d'organisation voit aussi les enquêtes des pôles de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], survey.id)

    @authenticate
    def test_pole_member_sees_pole_and_org_level_surveys(self):
        """
        Un RESPONDER rattaché à un pôle voit les enquêtes de ce pôle
        ET les enquêtes au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        pole_survey = SurveyFactory(organisation=org, pole=pole)
        org_survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [s["id"] for s in response.json()["results"]]
        self.assertIn(pole_survey.id, ids)
        self.assertIn(org_survey.id, ids)

    @authenticate
    def test_pole_member_cannot_see_other_pole_surveys(self):
        """
        Un membre d'un pôle ne voit pas les enquêtes des autres pôles de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        SurveyFactory(organisation=org, pole=other_pole)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()["results"], [])

    @authenticate
    def test_member_cannot_see_surveys_from_other_org(self):
        """
        Un membre ne voit pas les enquêtes d'une autre organisation
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        SurveyFactory(organisation=other_org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()["results"], [])

    @authenticate
    def test_enquete_inactive_non_retournee_dans_la_liste(self):
        """
        Une enquête désactivée (is_active=False) n'est pas retournée dans la liste,
        même pour un·e utilisateur·ice qui y aurait normalement accès
        """
        org = OrganisationFactory()
        enquete_active = SurveyFactory(organisation=org)
        enquete_inactive = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        enquete_inactive.deactivate()

        response = self.client.get(reverse("survey_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()["results"]]
        self.assertIn(enquete_active.id, ids)
        self.assertNotIn(enquete_inactive.id, ids)

    @authenticate
    def test_multiple_memberships_aggregate_surveys(self):
        """
        Un utilisateur avec plusieurs rôles voit les enquêtes de toutes ses organisations/pôles
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        survey_a = SurveyFactory(organisation=org_a)
        survey_b = SurveyFactory(organisation=org_b)
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.ADMIN)

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [s["id"] for s in response.json()["results"]]
        self.assertIn(survey_a.id, ids)
        self.assertIn(survey_b.id, ids)

    @authenticate
    def test_response_is_paginated(self):
        """
        La réponse inclut les clés de pagination count, next, previous et results
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        SurveyFactory(organisation=org)

        response = self.client.get(reverse("survey_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertIn("results", data)

    @authenticate
    def test_pagination_limit_offset(self):
        """
        Les paramètres limit et offset permettent de paginer les résultats
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        SurveyFactory.create_batch(5, organisation=org)

        response = self.client.get(reverse("survey_list_create"), {"limit": 2, "offset": 0}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 5)
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["next"])

    @authenticate
    def test_filtre_par_organisation(self):
        """
        Le filtre organisation retourne uniquement les enquêtes de l'organisation demandée
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        survey_a = SurveyFactory(organisation=org_a)
        SurveyFactory(organisation=org_b)
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.ADMIN)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.ADMIN)

        response = self.client.get(reverse("survey_list_create"), {"organisation": org_a.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], survey_a.id)

    @authenticate
    def test_filtre_created_after(self):
        """
        Le filtre created_after retourne uniquement les enquêtes créées après la date donnée
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        old_survey = SurveyFactory(organisation=org)
        old_survey.creation_date = timezone.datetime(2020, 1, 1, tzinfo=timezone.utc)
        old_survey.save()
        recent_survey = SurveyFactory(organisation=org)
        recent_survey.creation_date = timezone.datetime(2024, 6, 1, tzinfo=timezone.utc)
        recent_survey.save()

        response = self.client.get(
            reverse("survey_list_create"), {"created_after": "2023-01-01T00:00:00Z"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()["results"]]
        self.assertIn(recent_survey.id, ids)
        self.assertNotIn(old_survey.id, ids)

    @authenticate
    def test_filtre_created_before(self):
        """
        Le filtre created_before retourne uniquement les enquêtes créées avant la date donnée
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        old_survey = SurveyFactory(organisation=org)
        old_survey.creation_date = timezone.datetime(2020, 1, 1, tzinfo=timezone.utc)
        old_survey.save()
        recent_survey = SurveyFactory(organisation=org)
        recent_survey.creation_date = timezone.datetime(2024, 6, 1, tzinfo=timezone.utc)
        recent_survey.save()

        response = self.client.get(
            reverse("survey_list_create"), {"created_before": "2023-01-01T00:00:00Z"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()["results"]]
        self.assertIn(old_survey.id, ids)
        self.assertNotIn(recent_survey.id, ids)

    @authenticate
    def test_organisations_incluses_dans_la_reponse(self):
        """
        La réponse paginée inclut la clé "organisations" avec les organisations
        correspondant aux enquêtes retournées.
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        SurveyFactory(organisation=org)

        response = self.client.get(reverse("survey_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("organisations", data)
        org_ids = [o["id"] for o in data["organisations"]]
        self.assertIn(org.id, org_ids)

    @authenticate
    def test_organisations_ne_contient_que_les_orgs_des_resultats(self):
        """
        "organisations" ne liste que les organisations des enquêtes visibles dans la page,
        pas toutes les organisations existantes.
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.ADMIN)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.ADMIN)
        SurveyFactory(organisation=org_a)
        SurveyFactory(organisation=org_b)

        # On pagine pour n'obtenir qu'une enquête (celle de org_a)
        response = self.client.get(reverse("survey_list_create"), {"organisation": org_a.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        org_ids = [o["id"] for o in data["organisations"]]
        self.assertIn(org_a.id, org_ids)
        self.assertNotIn(org_b.id, org_ids)

    @authenticate
    def test_organisations_vide_si_aucun_resultat(self):
        """
        "organisations" est une liste vide quand aucune enquête n'est retournée.
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(reverse("survey_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["organisations"], [])
