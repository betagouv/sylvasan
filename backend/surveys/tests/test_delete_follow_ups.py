from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory
from surveys.models import SurveyFollowUp


def detail_url(survey, follow_up):
    return reverse("follow_up_retrieve_update_destroy", kwargs={"survey_pk": survey.pk, "pk": follow_up.pk})


class TestDeleteFollowUp(APITestCase):
    def test_non_authentifie_ne_peut_pas_supprimer_un_suivi(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_non_membre_ne_peut_pas_supprimer_un_suivi(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation reçoit un 404
        (le suivi est absent de son queryset)
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_responder_ne_peut_pas_supprimer_un_suivi(self):
        """
        Un·e RESPONDER reçoit un 403 en tentant de supprimer un suivi,
        même s'il ou elle y a accès en lecture
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_org_peut_supprimer_un_suivi_de_son_organisation(self):
        """
        Un·e ADMIN d'organisation peut supprimer un suivi — retourne 204
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_suivi_soft_deleted_existe_toujours_en_base(self):
        """
        Après suppression, le suivi existe toujours en base avec is_active=False
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        self.client.delete(detail_url(survey, suivi))
        self.assertTrue(SurveyFollowUp.objects.filter(pk=suivi.pk).exists())
        suivi.refresh_from_db()
        self.assertFalse(suivi.is_active)

    @authenticate
    def test_suivi_soft_deleted_exclu_du_queryset_actif(self):
        """
        Un suivi désactivé n'est plus retourné par SurveyFollowUp.objects.active()
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        self.client.delete(detail_url(survey, suivi))
        self.assertFalse(SurveyFollowUp.objects.active().filter(pk=suivi.pk).exists())

    @authenticate
    def test_admin_org_peut_supprimer_un_suivi_de_pole_dans_son_organisation(self):
        """
        Un·e ADMIN au niveau organisation peut supprimer un suivi rattaché
        à un pôle de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=None, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_admin_pole_peut_supprimer_un_suivi_de_son_pole(self):
        """
        Un·e ADMIN de pôle peut supprimer un suivi rattaché à son propre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_admin_pole_ne_peut_pas_supprimer_un_suivi_au_niveau_organisation(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer un suivi au niveau organisation (sans pôle) —
        il est absent de son queryset
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_pole_ne_peut_pas_supprimer_un_suivi_dun_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer un suivi rattaché à un autre pôle
        de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=autre_pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_autre_organisation_ne_peut_pas_supprimer_un_suivi(self):
        """
        Un·e ADMIN d'une autre organisation reçoit un 404
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=autre_org, membership_type=MembershipType.ADMIN)
        response = self.client.delete(detail_url(survey, suivi))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
