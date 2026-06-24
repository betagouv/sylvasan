import base64
import os

from django.test.utils import override_settings
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
    return reverse("response_retrieve_destroy", kwargs={"pk": response_id})


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

    @authenticate
    def test_org_admin_can_retrieve_response_for_pole_survey(self):
        """
        Un·e ADMIN au niveau organisation peut accéder aux réponses des enquêtes de pôles de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_pole_admin_can_retrieve_response_for_their_pole(self):
        """
        Un·e ADMIN de pôle peut accéder aux réponses des enquêtes de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], survey_response.id)

    @authenticate
    def test_pole_admin_cannot_retrieve_response_from_other_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas accéder aux réponses d'un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org, pole=other_pole))

        response = self.client.get(response_url(other_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_admin_cannot_retrieve_response_for_org_level_survey(self):
        """
        Un·e ADMIN de pôle ne peut pas accéder aux réponses des enquêtes au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
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
        photo_data = retrieve.json()["data"]["photo_arbre"]
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

        thumbnail = retrieve.json()["data"]["photo_arbre"][0]["thumbnail"]
        decoded = base64.b64decode(thumbnail)
        self.assertGreater(len(decoded), 0)

    @override_settings(HOSTNAME="hostname")
    @override_settings(SECURE=False)
    @authenticate
    def test_retrieve_file_url_is_valid(self):
        """
        Le URL du fichier est valide
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

        file_url = retrieve.json()["data"]["photo_arbre"][0]["file_url"]
        self.assertTrue(file_url.startswith("http://hostname"))


class TestResponseDataFieldNotCamelized(APITestCase):
    """
    Le champ "data" des réponses ne doit pas être transformé par le CamelCaseJSONRenderer.
    Les clés correspondent aux IDs des champs du schéma, qui peuvent contenir des underscores
    (ex. date_570). Les transformer en camelCase (date570) casserait l'interface.
    """

    @authenticate
    def test_field_id_with_underscore_digit_is_preserved_on_retrieve(self):
        """
        Un identifiant de champ comme "date_570" est retourné tel quel, sans être
        transformé en "date570" par le CamelCaseJSONRenderer.
        """
        org = OrganisationFactory()
        survey = SurveyFactory(
            organisation=org,
            json_schema={"fields": [{"id": "date_570", "type": "string", "label": "Date"}]},
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        survey_response = ResponseFactory(survey=survey, respondant=authenticate.user, data={"date_570": "2025-12-12"})

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertIn("date_570", data)
        self.assertNotIn("date570", data)
        self.assertEqual(data["date_570"], "2025-12-12")

    @authenticate
    def test_field_id_with_multiple_underscores_is_preserved_on_retrieve(self):
        """
        Un identifiant de champ comme "lieu_dit_commune" est retourné tel quel,
        sans être transformé en "lieuDitCommune".
        """
        org = OrganisationFactory()
        survey = SurveyFactory(
            organisation=org,
            json_schema={"fields": [{"id": "lieu_dit_commune", "type": "string", "label": "Lieu-dit"}]},
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        survey_response = ResponseFactory(
            survey=survey, respondant=authenticate.user, data={"lieu_dit_commune": "Les Granges"}
        )

        response = self.client.get(response_url(survey_response.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertIn("lieu_dit_commune", data)
        self.assertNotIn("lieuDitCommune", data)

    @authenticate
    def test_field_id_with_underscore_is_preserved_on_create(self):
        """
        Lors de la création, le champ "data" renvoyé dans le corps de la réponse 201
        conserve les clés telles qu'envoyées, sans camelisation.
        """
        org = OrganisationFactory()
        survey = SurveyFactory(
            organisation=org,
            json_schema={"fields": [{"id": "nom_observateur", "type": "string", "label": "Nom"}]},
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {"nom_observateur": "Alice"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()["data"]
        self.assertIn("nom_observateur", data)
        self.assertNotIn("nomObservateur", data)
        self.assertEqual(data["nom_observateur"], "Alice")
