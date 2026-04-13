from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase


def survey_payload(organisation, user, pole=None):
    payload = {
        "title": "Enquête test",
        "organisation": organisation.id,
        "created_by": user.id,
    }
    if pole:
        payload["pole"] = pole.id
    return payload


class TestCreateSurvey(APITestCase):
    def test_unauthenticated_cannot_create_survey(self):
        """
        Un utilisateur non authentifié ne peut pas créer d'enquête
        """
        org = OrganisationFactory()
        response = self.client.post(
            reverse("survey_list_create"),
            {"title": "Test", "organisation": org.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_cannot_create_survey(self):
        """
        Un utilisateur authentifié sans rôle ADMIN ne peut pas créer d'enquête
        """
        org = OrganisationFactory()
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_cannot_create_survey(self):
        """
        Un utilisateur avec le rôle RESPONDER ne peut pas créer d'enquête
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_manager_cannot_create_survey(self):
        """
        Un utilisateur avec le rôle MANAGER ne peut pas créer d'enquête
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_org_admin_can_create_survey_for_org(self):
        """
        Un ADMIN d'organisation peut créer une enquête au niveau de l'organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_org_admin_can_create_survey_for_pole_within_org(self):
        """
        Un ADMIN d'organisation peut créer une enquête pour n'importe quel pôle de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user, pole=pole),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_org_admin_cannot_create_survey_for_other_org(self):
        """
        Un ADMIN d'organisation ne peut pas créer une enquête pour une autre organisation
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(other_org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_pole_admin_can_create_survey_for_their_pole(self):
        """
        Un ADMIN de pôle peut créer une enquête pour son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user, pole=pole),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_pole_admin_cannot_create_org_level_survey(self):
        """
        Un ADMIN de pôle ne peut pas créer une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_pole_admin_cannot_create_survey_for_other_pole(self):
        """
        Un ADMIN de pôle ne peut pas créer une enquête pour un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("survey_list_create"),
            survey_payload(org, authenticate.user, pole=other_pole),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
