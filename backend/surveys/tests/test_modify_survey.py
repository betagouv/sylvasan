from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory
from surveys.surveytype import SurveyType


def valid_payload(survey):
    return {
        "organisation": survey.organisation.pk,
        "pole": survey.pole.pk if survey.pole else None,
        "title": survey.title,
        "json_schema": survey.json_schema,
        "survey_type": survey.survey_type,
        "campaign": survey.campaign.pk if survey.campaign else None,
    }


class TestModifySurveyPermissions(APITestCase):
    def test_non_authentifie_ne_peut_pas_modifier_une_enquete(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401 en tentant de modifier une enquête
        """
        survey = SurveyFactory()
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_non_membre_ne_peut_pas_modifier_une_enquete(self):
        """
        Un·e utilisateur·ice sans appartenance à l'organisation reçoit un 404
        (l'enquête est absente de son queryset)
        """
        survey = SurveyFactory()
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_responder_ne_peut_pas_modifier_une_enquete(self):
        """
        Un·e RESPONDER reçoit un 403 en tentant de modifier une enquête,
        même s'il ou elle y a accès en lecture
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.RESPONDER,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_org_peut_modifier_une_enquete_de_son_organisation(self):
        """
        Un·e ADMIN au niveau organisation peut modifier une enquête de son organisation
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_org_peut_modifier_une_enquete_de_pole(self):
        """
        Un·e ADMIN au niveau organisation peut modifier une enquête rattachée à un pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(
            user=authenticate.user,
            organisation=org,
            pole=None,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_pole_peut_modifier_enquete_de_son_pole(self):
        """
        Un·e ADMIN de pôle peut modifier une enquête rattachée à son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(
            user=authenticate.user,
            organisation=org,
            pole=pole,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_pole_ne_peut_pas_modifier_enquete_niveau_organisation(self):
        """
        Un·e ADMIN de pôle ne peut pas modifier une enquête au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=None)
        MembershipFactory(
            user=authenticate.user,
            organisation=org,
            pole=pole,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_pole_ne_peut_pas_modifier_enquete_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas modifier une enquête rattachée à un autre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=autre_pole)
        MembershipFactory(
            user=authenticate.user,
            organisation=org,
            pole=pole,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_autre_organisation_ne_peut_pas_modifier_une_enquete(self):
        """
        Un·e ADMIN d'une autre organisation reçoit un 404 en tentant de modifier
        une enquête qui ne lui appartient pas
        """
        survey = SurveyFactory()
        autre_org = OrganisationFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=autre_org,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}),
            data=valid_payload(survey),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestModifySurveyBehavior(APITestCase):
    def setUp(self):
        self.survey = SurveyFactory(
            title="Titre original",
            json_schema={"version": "1", "fields": []},
            survey_type=SurveyType.SELF_CONTAINED,
        )

    def _make_admin(self, user):
        MembershipFactory(
            user=user,
            organisation=self.survey.organisation,
            membership_type=MembershipType.ADMIN,
        )

    @authenticate
    def test_modification_retourne_200(self):
        """
        Un PUT valide retourne 200 avec les données mises à jour
        """
        self._make_admin(authenticate.user)
        payload = valid_payload(self.survey)
        payload["title"] = "Nouveau titre"
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": self.survey.pk}),
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_modification_met_a_jour_le_titre(self):
        """
        Après un PUT, le titre est bien mis à jour en base
        """
        self._make_admin(authenticate.user)
        payload = valid_payload(self.survey)
        payload["title"] = "Titre modifié"
        self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": self.survey.pk}),
            data=payload,
            format="json",
        )
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.title, "Titre modifié")

    @authenticate
    def test_modification_met_a_jour_le_schema(self):
        """
        Après un PUT, le json_schema est bien mis à jour en base
        """
        self._make_admin(authenticate.user)
        nouveau_schema = {"version": "2", "fields": [{"id": "champ1", "type": "string", "label": "Champ 1"}]}
        payload = valid_payload(self.survey)
        payload["json_schema"] = nouveau_schema
        self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": self.survey.pk}),
            data=payload,
            format="json",
        )
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.json_schema, nouveau_schema)

    @authenticate
    def test_modification_avec_titre_vide_retourne_400(self):
        """
        Un PUT avec un titre vide retourne 400
        """
        self._make_admin(authenticate.user)
        payload = valid_payload(self.survey)
        payload["title"] = ""
        response = self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": self.survey.pk}),
            data=payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_created_by_nest_pas_modifiable(self):
        """
        Le champ created_by est en lecture seule et ne peut pas être modifié via PUT
        """
        self._make_admin(authenticate.user)
        original_creator = self.survey.created_by
        payload = valid_payload(self.survey)
        payload["created_by"] = authenticate.user.pk
        self.client.put(
            reverse("survey_retrieve_update_destroy", kwargs={"pk": self.survey.pk}),
            data=payload,
            format="json",
        )
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.created_by, original_creator)
