from django.urls import reverse

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
        self.assertEqual(response.json(), [])

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
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey.id)

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
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey.id)

    @authenticate
    def test_pole_member_sees_only_their_pole_surveys(self):
        """
        Un membre d'un pôle voit uniquement les enquêtes de ce pôle, pas les enquêtes au niveau organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        pole_survey = SurveyFactory(organisation=org, pole=pole)
        SurveyFactory(organisation=org, pole=None)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], pole_survey.id)

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

        self.assertEqual(response.json(), [])

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

        self.assertEqual(response.json(), [])

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
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.MANAGER)

        response = self.client.get(reverse("survey_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [s["id"] for s in response.json()]
        self.assertIn(survey_a.id, ids)
        self.assertIn(survey_b.id, ids)
