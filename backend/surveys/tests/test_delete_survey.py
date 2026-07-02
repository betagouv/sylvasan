from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from responses.factories import ResponseFactory
from responses.models import Response
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory
from surveys.models import Survey


class TestSoftDeleteSurvey(APITestCase):
    def test_non_authentifie_ne_peut_pas_supprimer_une_enquete(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401 en tentant de supprimer une enquête
        """
        survey = SurveyFactory()
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_admin_peut_supprimer_une_enquete_de_son_organisation(self):
        """
        Un·e ADMIN peut supprimer (désactiver) une enquête de son organisation — retourne 204
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_enquete_soft_deletee_existe_toujours_en_base(self):
        """
        Après suppression, l'enquête existe toujours en base avec is_active=False
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))

        survey.refresh_from_db()
        self.assertFalse(survey.is_active)
        self.assertTrue(Survey.objects.filter(pk=survey.pk).exists())

    @authenticate
    def test_enquete_soft_deletee_exclue_du_queryset_actif(self):
        """
        Une enquête désactivée n'est plus retournée par Survey.objects.active()
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))

        self.assertFalse(Survey.objects.active().filter(pk=survey.pk).exists())

    @authenticate
    def test_suppression_enquete_desactive_aussi_ses_reponses(self):
        """
        Supprimer une enquête désactive également toutes ses réponses
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        reponse_1 = ResponseFactory(survey=survey)
        reponse_2 = ResponseFactory(survey=survey)

        self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))

        reponse_1.refresh_from_db()
        reponse_2.refresh_from_db()
        self.assertFalse(reponse_1.is_active)
        self.assertFalse(reponse_2.is_active)

    @authenticate
    def test_suppression_enquete_ne_supprime_pas_les_reponses_en_base(self):
        """
        Les réponses désactivées existent toujours en base après suppression de l'enquête
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.ADMIN,
        )
        reponse = ResponseFactory(survey=survey)

        self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))

        self.assertTrue(Response.objects.filter(pk=reponse.pk).exists())

    @authenticate
    def test_non_membre_ne_peut_pas_supprimer_une_enquete(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation reçoit un 404
        (l'enquête est absente de son queryset)
        """
        survey = SurveyFactory()
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_responder_ne_peut_pas_supprimer_une_enquete(self):
        """
        Un·e RESPONDER reçoit un 403 en tentant de supprimer une enquête,
        même s'il ou elle y a accès en lecture
        """
        survey = SurveyFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=survey.organisation,
            membership_type=MembershipType.RESPONDER,
        )
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_org_peut_supprimer_une_enquete_de_pole(self):
        """
        Un·e ADMIN au niveau organisation (pole=None) peut supprimer une enquête
        rattachée à un pôle de cette organisation
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
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_admin_pole_peut_supprimer_enquete_de_son_pole(self):
        """
        Un·e ADMIN de pôle peut supprimer une enquête rattachée à son pôle
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
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_admin_pole_ne_peut_pas_supprimer_enquete_niveau_organisation(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer une enquête au niveau organisation (sans pôle)
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
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_pole_ne_peut_pas_supprimer_enquete_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer une enquête rattachée à un autre pôle
        de la même organisation
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
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_membre_autre_organisation_ne_peut_pas_supprimer_une_enquete(self):
        """
        Un·e ADMIN d'une autre organisation reçoit un 404 en tentant
        de supprimer une enquête qui ne lui appartient pas
        """
        survey = SurveyFactory()
        autre_org = OrganisationFactory()
        MembershipFactory(
            user=authenticate.user,
            organisation=autre_org,
            membership_type=MembershipType.ADMIN,
        )
        response = self.client.delete(reverse("survey_retrieve_update_destroy", kwargs={"pk": survey.pk}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
