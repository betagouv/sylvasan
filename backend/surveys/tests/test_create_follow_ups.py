from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from users.factories import UserFactory

from surveys.factories import SurveyFactory
from surveys.models import SurveyFollowUp


def list_url(survey):
    return reverse("follow_up_list_create", kwargs={"survey_pk": survey.pk})


def follow_up_payload(org, pole=None):
    payload = {
        "organisation": org.id,
        "title": "Suivi test",
        "action_label": "Envoyer au laboratoire",
    }
    if pole:
        payload["pole"] = pole.id
    return payload


class TestCreateFollowUp(APITestCase):
    def test_non_authentifie_ne_peut_pas_creer_un_suivi(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit un 401
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_sans_membership_ne_peut_pas_creer_un_suivi(self):
        """
        Un·e utilisateur·ice sans rôle dans l'organisation reçoit un 403
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_ne_peut_pas_creer_un_suivi(self):
        """
        Un·e RESPONDER ne peut pas créer de suivi, même dans son organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_org_peut_creer_un_suivi_au_niveau_organisation(self):
        """
        Un·e ADMIN d'organisation peut créer un suivi au niveau de l'organisation (sans pôle)
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_admin_org_peut_creer_un_suivi_pour_un_pole_de_son_organisation(self):
        """
        Un·e ADMIN d'organisation peut créer un suivi rattaché à un pôle de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org, pole=pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_admin_org_ne_peut_pas_creer_un_suivi_pour_une_autre_organisation(self):
        """
        Un·e ADMIN d'organisation ne peut pas créer un suivi pour une autre organisation
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(autre_org), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_pole_peut_creer_un_suivi_pour_son_pole(self):
        """
        Un·e ADMIN de pôle peut créer un suivi rattaché à son propre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org, pole=pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate
    def test_admin_pole_ne_peut_pas_creer_un_suivi_au_niveau_organisation(self):
        """
        Un·e ADMIN de pôle ne peut pas créer un suivi au niveau organisation (sans pôle)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_pole_ne_peut_pas_creer_un_suivi_pour_un_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas créer un suivi pour un autre pôle de la même organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org, pole=autre_pole), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_suivi_cree_rattache_a_lenquete_de_lurl(self):
        """
        Le suivi créé est automatiquement rattaché à l'enquête désignée par l'URL,
        indépendamment de tout paramètre du corps de la requête
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        suivi = SurveyFollowUp.objects.get(pk=response.data["id"])
        self.assertEqual(suivi.parent_survey, survey)

    @authenticate
    def test_created_by_est_renseigne_automatiquement(self):
        """
        Le champ created_by est automatiquement renseigné avec l'utilisateur authentifié
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.post(list_url(survey), follow_up_payload(org), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], authenticate.user.id)

    @authenticate
    def test_created_by_du_frontend_est_ignore(self):
        """
        Une valeur de created_by fournie dans le corps de la requête est ignorée
        """
        org = OrganisationFactory()
        autre_utilisateur = UserFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        payload = follow_up_payload(org)
        payload["created_by"] = autre_utilisateur.id
        response = self.client.post(list_url(survey), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], authenticate.user.id)
