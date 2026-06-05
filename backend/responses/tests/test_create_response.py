import base64
import os

from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from users.factories import UserFactory

from responses.models import ResponseImage

_TEST_FILES = os.path.join(os.path.dirname(__file__), "files")


def _b64(filename):
    with open(os.path.join(_TEST_FILES, filename), "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _image_survey(**kwargs):
    return SurveyFactory(
        json_schema={"fields": [{"id": "photo_arbre", "ui": {"widget": "image"}}]},
        **kwargs,
    )


def response_payload(survey):
    return {
        "survey": survey.id,
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
            response_payload(survey),
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
            response_payload(survey),
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
            response_payload(survey),
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
            response_payload(survey),
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
            response_payload(survey),
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
            response_payload(other_survey),
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
            response_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_pole_responder_can_create_response_for_org_level_survey(self):
        """
        Un·e RESPONDER de pôle peut répondre à une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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
            response_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_respondant_is_set_to_authenticated_user(self):
        """
        Le champ respondant est automatiquement renseigné avec l'utilisateur authentifié
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            response_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["respondant"], authenticate.user.id)

    @authenticate
    def test_respondant_ignores_frontend_value(self):
        """
        Une valeur de respondant fournie par le frontend est ignorée
        """
        survey = SurveyFactory()
        other_user = UserFactory()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        payload = response_payload(survey)
        payload["respondant"] = other_user.id
        response = self.client.post(
            reverse("response_list_create"),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["respondant"], authenticate.user.id)


class TestCreateResponseWithImages(APITestCase):
    def _post_with_images(self, survey, *filenames):
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        return self.client.post(
            reverse("response_list_create"),
            {
                "survey": survey.id,
                "data": {"photo_arbre": [{"file": _b64(f)} for f in filenames]},
            },
            format="json",
        )

    @authenticate
    def test_image_field_creates_response_image_objects(self):
        """
        Soumettre des images dans un champ image crée des objets ResponseImage en base de données
        """
        response = self._post_with_images(_image_survey(), "Blue.jpg", "Green.jpg")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ResponseImage.objects.count(), 2)

    @authenticate
    def test_image_data_replaced_with_id_stub(self):
        """
        Après soumission, le champ image dans data contient des objets {id} uniquement.
        L'enrichissement (thumbnail, fileUrl) est fait à la lecture via FullResponseSerializer.
        """
        response = self._post_with_images(_image_survey(), "Blue.jpg")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        photo_data = response.json()["data"]["photoArbre"]
        self.assertEqual(len(photo_data), 1)
        self.assertIn("id", photo_data[0])
        self.assertNotIn("file", photo_data[0])
        self.assertNotIn("thumbnail", photo_data[0])

    @authenticate
    def test_oversized_image_returns_400(self):
        """
        Un payload base64 dépassant 2 Mo est rejeté avec une 400
        """
        survey = _image_survey()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        # 3 Mo de données brutes → ~4 Mo en base64, au-dessus du seuil de 2 Mo
        oversized = base64.b64encode(b"x" * (3 * 1024 * 1024)).decode("utf-8")
        response = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {"photo_arbre": [{"file": oversized}]}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_invalid_base64_returns_400(self):
        """
        Des données base64 malformées sont rejetées avec une 400
        """
        survey = _image_survey()
        MembershipFactory(
            user=authenticate.user, organisation=survey.organisation, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            {"survey": survey.id, "data": {"photo_arbre": [{"file": "ceci-n'est-pas-du-base64!"}]}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
