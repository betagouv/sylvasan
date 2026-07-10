from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory


def list_url(survey):
    return reverse("follow_up_list_create", kwargs={"survey_pk": survey.pk})


class TestListFollowUps(APITestCase):
    def test_non_authentifie_ne_peut_pas_lister_les_suivis(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401
        """
        survey = SurveyFactory()
        response = self.client.get(list_url(survey), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_sans_membership_retourne_liste_vide(self):
        """
        Un·e utilisateur·ice sans rôle ne voit aucun suivi
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        SurveyFollowUpFactory(organisation=org, parent_survey=survey)

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_membre_org_voit_les_suivis_au_niveau_organisation(self):
        """
        Un·e membre d'organisation voit les suivis rattachés directement à l'organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertIn(suivi.id, ids)

    @authenticate
    def test_membre_pole_voit_les_suivis_de_son_pole(self):
        """
        Un·e RESPONDER rattaché·e à un pôle voit les suivis de ce pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertIn(suivi.id, ids)

    @authenticate
    def test_membre_pole_voit_aussi_les_suivis_au_niveau_organisation(self):
        """
        Un·e RESPONDER rattaché·e à un pôle voit également les suivis au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        suivi_pole = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        suivi_org = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertIn(suivi_pole.id, ids)
        self.assertIn(suivi_org.id, ids)

    @authenticate
    def test_membre_pole_ne_voit_pas_les_suivis_des_autres_poles(self):
        """
        Un·e membre d'un pôle ne voit pas les suivis rattachés à un autre pôle
        de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        SurveyFollowUpFactory(organisation=org, pole=autre_pole, parent_survey=survey)
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_membre_ne_voit_pas_les_suivis_dune_autre_organisation(self):
        """
        Un·e membre d'une organisation ne voit pas les suivis appartenant
        à une autre organisation
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        SurveyFollowUpFactory(organisation=autre_org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_suivi_inactif_exclu_de_la_liste(self):
        """
        Un suivi désactivé (is_active=False) n'est pas retourné dans la liste
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        suivi_actif = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        suivi_inactif = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        suivi_inactif.deactivate()

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertIn(suivi_actif.id, ids)
        self.assertNotIn(suivi_inactif.id, ids)

    @authenticate
    def test_liste_filtree_par_enquete(self):
        """
        Seuls les suivis rattachés à l'enquête demandée sont retournés,
        pas ceux d'une autre enquête du même utilisateur
        """
        org = OrganisationFactory()
        survey_a = SurveyFactory(organisation=org)
        survey_b = SurveyFactory(organisation=org)
        suivi_a = SurveyFollowUpFactory(organisation=org, parent_survey=survey_a)
        SurveyFollowUpFactory(organisation=org, parent_survey=survey_b)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(list_url(survey_a), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertEqual(ids, [suivi_a.id])

    @authenticate
    def test_plusieurs_memberships_aggregent_les_suivis(self):
        """
        Un·e utilisateur·ice avec des rôles dans plusieurs organisations
        voit les suivis de toutes ses organisations accessibles
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        survey = SurveyFactory()
        suivi_a = SurveyFollowUpFactory(organisation=org_a, parent_survey=survey)
        suivi_b = SurveyFollowUpFactory(organisation=org_b, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.ADMIN)

        response = self.client.get(list_url(survey), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.json()]
        self.assertIn(suivi_a.id, ids)
        self.assertIn(suivi_b.id, ids)
