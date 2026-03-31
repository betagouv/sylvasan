from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory


def survey_url(survey_id):
    return reverse("survey_retrieve", kwargs={"pk": survey_id})


class TestRetrieveSurvey(APITestCase):
    def test_unauthenticated_cannot_retrieve_survey(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        survey = SurveyFactory()
        response = self.client.get(survey_url(survey.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_cannot_retrieve_survey(self):
        """
        Un·e utilisateur·ice sans rôle ne peut pas accéder à une enquête — reçoit une 404
        """
        survey = SurveyFactory()
        response = self.client.get(survey_url(survey.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_nonexistent_survey_returns_404(self):
        """
        Une requête vers un identifiant inexistant retourne une 404
        """
        response = self.client.get(survey_url(99999), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Role RESPONDER

    @authenticate
    def test_org_responder_can_retrieve_org_survey(self):
        """
        Un·e RESPONDER au niveau organisation peut accéder à une enquête de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_org_responder_can_retrieve_pole_survey_within_org(self):
        """
        Un·e RESPONDER au niveau organisation peut accéder à une enquête d'un pôle de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_org_responder_cannot_retrieve_survey_from_other_org(self):
        """
        Un·e RESPONDER ne peut pas accéder à une enquête d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        other_survey = SurveyFactory()

        response = self.client.get(survey_url(other_survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_responder_can_retrieve_their_pole_survey(self):
        """
        Un·e RESPONDER de pôle peut accéder à une enquête de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_pole_responder_cannot_retrieve_org_level_survey(self):
        """
        Un·e RESPONDER de pôle ne peut pas accéder à une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_responder_cannot_retrieve_survey_from_other_pole(self):
        """
        Un·e RESPONDER de pôle ne peut pas accéder à une enquête d'un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=other_pole)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # role MANAGER

    @authenticate
    def test_org_manager_can_retrieve_org_survey(self):
        """
        Un·e MANAGER au niveau organisation peut accéder à une enquête de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_org_manager_can_retrieve_pole_survey_within_org(self):
        """
        Un·e MANAGER au niveau organisation peut accéder à une enquête d'un pôle de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_org_manager_cannot_retrieve_survey_from_other_org(self):
        """
        Un·e MANAGER ne peut pas accéder à une enquête d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        other_survey = SurveyFactory()

        response = self.client.get(survey_url(other_survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_manager_can_retrieve_their_pole_survey(self):
        """
        Un·e MANAGER de pôle peut accéder à une enquête de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_pole_manager_cannot_retrieve_org_level_survey(self):
        """
        Un·e MANAGER de pôle ne peut pas accéder à une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_manager_cannot_retrieve_survey_from_other_pole(self):
        """
        Un·e MANAGER de pôle ne peut pas accéder à une enquête d'un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=other_pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Role ADMIN

    @authenticate
    def test_org_admin_can_retrieve_org_survey(self):
        """
        Un·e ADMIN au niveau organisation peut accéder à une enquête de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(survey_url(survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey.id)

    @authenticate
    def test_org_admin_cannot_retrieve_survey_from_other_org(self):
        """
        Un·e ADMIN ne peut pas accéder à une enquête d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        other_survey = SurveyFactory()

        response = self.client.get(survey_url(other_survey.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
