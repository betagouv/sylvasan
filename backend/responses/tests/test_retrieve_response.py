import base64
import os

from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory

from responses.factories import ResponseFactory

_TEST_FILES = os.path.join(os.path.dirname(__file__), "files")


def _b64(filename):
    with open(os.path.join(_TEST_FILES, filename), "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def response_url(response_id):
    return reverse("response_retrieve", kwargs={"pk": response_id})


class TestRetrieveResponse(APITestCase):
    def test_unauthenticated_cannot_retrieve_response(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        survey_response = ResponseFactory()
        response = self.client.get(response_url(survey_response.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_cannot_retrieve_response(self):
        """
        Un·e utilisateur·ice sans rôle ne peut pas accéder à une réponse — reçoit une 404
        """
        survey_response = ResponseFactory()
        response = self.client.get(response_url(survey_response.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_nonexistent_response_returns_404(self):
        """
        Une requête vers un identifiant inexistant retourne une 404
        """
        response = self.client.get(response_url(99999), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Role RESPONDER

    @authenticate
    def test_responder_can_retrieve_their_own_response(self):
        """
        Un·e RESPONDER peut accéder à une réponse qu'il ou elle a créée
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        survey_response = ResponseFactory(survey=survey, respondant=authenticate.user)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_responder_cannot_retrieve_other_users_response(self):
        """
        Un·e RESPONDER ne peut pas accéder à la réponse d'un·e autre utilisateur·ice
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        other_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Role MANAGER

    @authenticate
    def test_org_manager_can_retrieve_any_response_in_org(self):
        """
        Un·e MANAGER au niveau organisation peut accéder à n'importe quelle réponse de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_org_manager_can_retrieve_response_for_pole_survey(self):
        """
        Un·e MANAGER au niveau organisation peut accéder aux réponses des enquêtes de pôles de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_org_manager_cannot_retrieve_response_from_other_org(self):
        """
        Un·e MANAGER ne peut pas accéder à une réponse d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        other_response = ResponseFactory(survey=SurveyFactory())

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_manager_can_retrieve_response_for_their_pole(self):
        """
        Un·e MANAGER de pôle peut accéder aux réponses des enquêtes de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_pole_manager_cannot_retrieve_response_from_other_pole(self):
        """
        Un·e MANAGER de pôle ne peut pas accéder aux réponses d'un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org, pole=other_pole))

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_manager_cannot_retrieve_response_for_org_level_survey(self):
        """
        Un·e MANAGER de pôle ne peut pas accéder aux réponses des enquêtes au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org, pole=None))

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Role ADMIN

    @authenticate
    def test_org_admin_can_retrieve_any_response_in_org(self):
        """
        Un·e ADMIN au niveau organisation peut accéder à n'importe quelle réponse de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_org_admin_cannot_retrieve_response_from_other_org(self):
        """
        Un·e ADMIN ne peut pas accéder à une réponse d'une autre organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        other_response = ResponseFactory(survey=SurveyFactory())

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRetrieveResponseWithImages(APITestCase):
    @authenticate
    def test_retrieve_returns_thumbnail_references_not_base64(self):
        """
        Récupérer une réponse avec des images retourne des objets {id, thumbnail}
        dans le champ data, sans les données base64 originales
        """
        org = OrganisationFactory()
        survey = SurveyFactory(
            organisation=org,
            json_schema={"fields": [{"id": "photo_arbre", "ui": {"widget": "image"}}]},
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        create = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {"photo_arbre": [{"file": _b64("Blue.jpg")}]}},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)

        retrieve = self.client.get(response_url(create.json()["id"]), format="json")

        self.assertEqual(retrieve.status_code, status.HTTP_200_OK)
        photo_data = retrieve.json()["data"]["photoArbre"]
        self.assertEqual(len(photo_data), 1)
        self.assertIn("id", photo_data[0])
        self.assertIn("thumbnail", photo_data[0])
        self.assertNotIn("file", photo_data[0])

    @authenticate
    def test_retrieve_thumbnail_is_valid_base64(self):
        """
        La miniature dans la réponse récupérée est une chaîne base64 valide
        """
        org = OrganisationFactory()
        survey = SurveyFactory(
            organisation=org,
            json_schema={"fields": [{"id": "photo_arbre", "ui": {"widget": "image"}}]},
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        create = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {"photo_arbre": [{"file": _b64("Green.jpg")}]}},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)

        retrieve = self.client.get(response_url(create.json()["id"]), format="json")

        thumbnail = retrieve.json()["data"]["photoArbre"][0]["thumbnail"]
        decoded = base64.b64decode(thumbnail)
        self.assertGreater(len(decoded), 0)
