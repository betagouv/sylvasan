import base64
import os

from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory
from users.factories import UserFactory

from responses.factories import ResponseFactory
from responses.models import Response, ResponseImage

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
        photo_data = response.json()["data"]["photo_arbre"]
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


def follow_up_response_payload(follow_up, parent_response):
    return {
        "survey_follow_up": follow_up.id,
        "parent_response": parent_response.id,
        "data": {},
    }


class TestCreateFollowUpResponse(APITestCase):
    def test_non_authentifie_ne_peut_pas_creer_une_reponse_de_suivi(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_sans_membership_ne_peut_pas_creer_une_reponse_de_suivi(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation reçoit un 403
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_ne_peut_pas_creer_une_reponse_de_suivi(self):
        """
        Un·e ADMIN ne peut pas créer une réponse de suivi, seuls les RESPONDER peuvent
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_org_peut_creer_une_reponse_pour_un_suivi_org(self):
        """
        Un·e RESPONDER au niveau de l'organisation peut créer une réponse
        pour un suivi rattaché à cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_responder_org_peut_creer_une_reponse_pour_un_suivi_de_pole(self):
        """
        Un·e RESPONDER au niveau de l'organisation peut créer une réponse
        pour un suivi rattaché à un pôle de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_responder_pole_peut_creer_une_reponse_pour_le_suivi_de_son_pole(self):
        """
        Un·e RESPONDER de pôle peut créer une réponse pour un suivi de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_responder_pole_peut_creer_une_reponse_pour_un_suivi_org(self):
        """
        Un·e RESPONDER de pôle peut créer une réponse pour un suivi au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_responder_pole_ne_peut_pas_creer_une_reponse_pour_un_suivi_dun_autre_pole(self):
        """
        Un·e RESPONDER de pôle ne peut pas créer une réponse pour un suivi rattaché à un autre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=autre_pole, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_autre_org_ne_peut_pas_creer_une_reponse_de_suivi(self):
        """
        Un·e RESPONDER d'une autre organisation ne peut pas créer une réponse de suivi
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=autre_org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_reponse_de_suivi_creee_sans_enquete_associee(self):
        """
        Une réponse de suivi n'a pas de champ survey — il est null en base
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = Response.objects.get(pk=response.data["id"])
        self.assertIsNone(obj.survey_id)
        self.assertEqual(obj.survey_follow_up_id, follow_up.id)
        self.assertEqual(obj.parent_response_id, parent.id)

    @authenticate
    def test_respondant_est_renseigne_automatiquement(self):
        """
        Le champ respondant est automatiquement renseigné avec l'utilisateur authentifié
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            follow_up_response_payload(follow_up, parent),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["respondant"], authenticate.user.id)

    @authenticate
    def test_survey_follow_up_non_entier_retourne_403(self):
        """
        Envoyer une valeur non entière pour survey_follow_up (ex: "abc") ne provoque pas
        un crash HTTP 500 — la permission retourne False → 403
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            {"survey_follow_up": "abc", "parent_response": 1, "data": {}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_reponse_de_suivi_sans_parent_response_retourne_400(self):
        """
        Créer une réponse de suivi sans fournir parent_response retourne une 400 —
        ce champ est obligatoire pour les réponses de suivi
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            {"survey_follow_up": follow_up.id, "data": {}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_parent_response_appartenant_a_une_autre_enquete_retourne_400(self):
        """
        Lier une réponse de suivi à une réponse parente issue d'une autre enquête retourne une 400.
        Cela évite les liaisons cross-survey.
        """
        org = OrganisationFactory()
        survey_1 = SurveyFactory(organisation=org)
        survey_2 = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey_1)
        parent_from_other_survey = ResponseFactory(survey=survey_2)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("response_list_create"),
            {
                "survey_follow_up": follow_up.id,
                "parent_response": parent_from_other_survey.id,
                "data": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
