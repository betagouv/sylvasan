from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory


def response_payload(survey, user):
    return {
        "survey": survey.id,
        "respondant": user.id,
        "data": {},
    }


class TestCreateResponse(APITestCase):
    def test_unauthenticated_cannot_create_response(self):
        """
        Un·e utilisateur·ice non authentifié·e ne peut pas créer une réponse
        """
        survey = SurveyFactory()
        response = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_cannot_create_response(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation ne peut pas créer une réponse
        """
        survey = SurveyFactory()
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_membership_cannot_create_response(self):
        """
        Un·e utilisateur·ice avec le rôle ADMIN ne peut pas créer une réponse
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.ADMIN
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_manager_membership_cannot_create_response(self):
        """
        Un·e utilisateur·ice avec le rôle MANAGER ne peut pas créer une réponse
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.MANAGER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_org_responder_can_create_response_for_org_survey(self):
        """
        Un·e RESPONDER au niveau de l'organisation peut répondre à une enquête de l'organisation
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_org_responder_can_create_response_for_pole_survey(self):
        """
        Un·e RESPONDER au niveau de l'organisation peut répondre à une enquête d'un pôle de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_org_responder_cannot_create_response_for_other_org_survey(self):
        """
        Un·e RESPONDER d'une organisation ne peut pas répondre à une enquête d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        other_survey = SurveyFactory()
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(other_survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_pole_responder_can_create_response_for_their_pole_survey(self):
        """
        Un·e RESPONDER de pôle peut répondre à une enquête de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_pole_responder_cannot_create_response_for_org_level_survey(self):
        """
        Un·e RESPONDER de pôle ne peut pas répondre à une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_pole_responder_cannot_create_response_for_other_pole_survey(self):
        """
        Un·e RESPONDER de pôle ne peut pas répondre à une enquête d'un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=other_pole)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
