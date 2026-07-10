from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory


def detail_url(survey, follow_up):
    return reverse("follow_up_retrieve_update_destroy", kwargs={"survey_pk": survey.pk, "pk": follow_up.pk})


def follow_up_payload(org, pole=None):
    payload = {
        "organisation": org.id,
        "title": "Suivi modifié",
        "action_label": "Retour du laboratoire",
    }
    if pole:
        payload["pole"] = pole.id
    return payload


class TestModifyFollowUp(APITestCase):
    def test_non_authentifie_ne_peut_pas_modifier_un_suivi(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_non_membre_ne_peut_pas_modifier_un_suivi(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation reçoit un 404
        (le suivi est absent de son queryset)
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_responder_ne_peut_pas_modifier_un_suivi(self):
        """
        Un·e RESPONDER reçoit un 403 en tentant de modifier un suivi,
        même s'il ou elle y a accès en lecture
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_org_peut_modifier_un_suivi_de_son_organisation(self):
        """
        Un·e ADMIN d'organisation peut modifier un suivi au niveau organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_org_peut_modifier_un_suivi_de_pole_dans_son_organisation(self):
        """
        Un·e ADMIN au niveau organisation peut modifier un suivi rattaché
        à un pôle de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=None, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org, pole=pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_pole_peut_modifier_un_suivi_de_son_pole(self):
        """
        Un·e ADMIN de pôle peut modifier un suivi rattaché à son propre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org, pole=pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @authenticate
    def test_admin_pole_ne_peut_pas_modifier_un_suivi_au_niveau_organisation(self):
        """
        Un·e ADMIN de pôle ne peut pas modifier un suivi au niveau organisation (sans pôle) —
        ce suivi est absent de son queryset
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_pole_ne_peut_pas_modifier_un_suivi_dun_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas modifier un suivi rattaché à un autre pôle
        de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=autre_pole, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org, pole=autre_pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_autre_organisation_ne_peut_pas_modifier_un_suivi(self):
        """
        Un·e ADMIN d'une autre organisation reçoit un 404
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=autre_org, membership_type=MembershipType.ADMIN)
        response = self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_modification_partielle_avec_patch(self):
        """
        Une modification partielle (PATCH) avec un seul champ fonctionne correctement
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.patch(detail_url(survey, suivi), {"title": "Nouveau titre"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suivi.refresh_from_db()
        self.assertEqual(suivi.title, "Nouveau titre")

    @authenticate
    def test_modification_persistee_en_base(self):
        """
        Les modifications sont bien persistées en base de données
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        self.client.put(detail_url(survey, suivi), follow_up_payload(org), format="json")
        suivi.refresh_from_db()
        self.assertEqual(suivi.title, "Suivi modifié")
        self.assertEqual(suivi.action_label, "Retour du laboratoire")
