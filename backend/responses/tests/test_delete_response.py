from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory

from responses.factories import ResponseFactory
from responses.models import Response


def response_url(response_id):
    return reverse("response_retrieve_destroy", kwargs={"pk": response_id})


class TestDeleteResponse(APITestCase):
    def test_unauthenticated_cannot_delete_response(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        survey_response = ResponseFactory()
        response = self.client.delete(response_url(survey_response.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_cannot_delete_response(self):
        """
        Un·e utilisateur·ice sans rôle ne peut pas accéder à la réponse — reçoit une 404
        """
        survey_response = ResponseFactory()
        response = self.client.delete(response_url(survey_response.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_nonexistent_response_returns_404(self):
        """
        Une requête vers un identifiant inexistant retourne une 404
        """
        response = self.client.delete(response_url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Rôle RESPONDER

    @authenticate
    def test_responder_cannot_delete_their_own_response(self):
        """
        Un·e RESPONDER ne peut pas supprimer sa propre réponse — reçoit une 403
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        survey_response = ResponseFactory(survey=survey, respondant=authenticate.user)

        response = self.client.delete(response_url(survey_response.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_cannot_delete_others_response(self):
        """
        Un·e RESPONDER ne peut pas voir (ni supprimer) la réponse d'un·e autre utilisateur·ice — reçoit une 404
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        other_response = ResponseFactory(survey=survey)

        response = self.client.delete(response_url(other_response.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Rôle ADMIN au niveau organisation

    @authenticate
    def test_org_admin_can_delete_any_response_in_org(self):
        """
        Un·e ADMIN au niveau organisation peut supprimer n'importe quelle réponse de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.delete(response_url(survey_response.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_org_admin_can_delete_response_from_pole_survey(self):
        """
        Un·e ADMIN au niveau organisation peut supprimer des réponses d'enquêtes de pôles de son organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.delete(response_url(survey_response.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_org_admin_cannot_delete_response_from_other_org(self):
        """
        Un·e ADMIN ne peut pas supprimer une réponse d'une autre organisation — reçoit une 404
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        other_response = ResponseFactory(survey=SurveyFactory())

        response = self.client.delete(response_url(other_response.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Rôle ADMIN au niveau pôle

    @authenticate
    def test_pole_admin_can_delete_response_from_their_pole(self):
        """
        Un·e ADMIN de pôle peut supprimer des réponses d'enquêtes de son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.delete(response_url(survey_response.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_pole_admin_cannot_delete_response_from_other_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer les réponses d'un autre pôle — reçoit une 404
        (la réponse n'est pas visible dans son queryset)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org, pole=other_pole))

        response = self.client.delete(response_url(other_response.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_pole_admin_cannot_delete_response_from_org_level_survey(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer les réponses d'enquêtes au niveau organisation — reçoit une 404
        (la réponse n'est pas visible dans son queryset)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        org_level_response = ResponseFactory(survey=SurveyFactory(organisation=org, pole=None))

        response = self.client.delete(response_url(org_level_response.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestSoftDeleteBehavior(APITestCase):
    @authenticate
    def test_delete_returns_204_no_content(self):
        """
        La suppression réussie retourne un 204 sans corps de réponse
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.delete(response_url(survey_response.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)

    @authenticate
    def test_delete_sets_is_active_to_false(self):
        """
        La suppression est un soft-delete : is_active passe à False, l'enregistrement est conservé en base
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        self.client.delete(response_url(survey_response.id))

        survey_response.refresh_from_db()
        self.assertFalse(survey_response.is_active)

    @authenticate
    def test_deleted_response_no_longer_retrievable(self):
        """
        Une réponse supprimée ne peut plus être récupérée via GET — reçoit une 404
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        self.client.delete(response_url(survey_response.id))
        get_response = self.client.get(response_url(survey_response.id))

        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_deleted_response_no_longer_in_list(self):
        """
        Une réponse supprimée n'apparaît plus dans la liste des réponses
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        self.client.delete(response_url(survey_response.id))
        list_response = self.client.get(reverse("response_list_create"))

        ids = [r["id"] for r in list_response.json()["results"]]
        self.assertNotIn(survey_response.id, ids)

    @authenticate
    def test_second_delete_on_same_response_returns_404(self):
        """
        Supprimer une réponse déjà supprimée retourne une 404
        (la réponse inactive est absente du queryset)
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        self.client.delete(response_url(survey_response.id))
        second_delete = self.client.delete(response_url(survey_response.id))

        self.assertEqual(second_delete.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_hard_delete_is_not_performed(self):
        """
        La suppression ne retire pas l'enregistrement de la base — il reste accessible via le manager non filtré
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response = ResponseFactory(survey=survey)

        self.client.delete(response_url(survey_response.id))

        self.assertTrue(Response.objects.filter(pk=survey_response.pk).exists())


class TestDeleteFollowUpResponse(APITestCase):
    def _make_follow_up_response(self, org, pole=None):
        """Crée une réponse parente et une réponse de suivi associée."""
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, pole=pole, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        return ResponseFactory(survey=None, survey_follow_up=follow_up, parent_response=parent), follow_up

    @authenticate
    def test_admin_org_peut_supprimer_une_reponse_de_suivi(self):
        """
        Un·e ADMIN au niveau organisation peut supprimer une réponse de suivi de son organisation
        """
        org = OrganisationFactory()
        suivi_reponse, _ = self._make_follow_up_response(org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.delete(response_url(suivi_reponse.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_responder_ne_peut_pas_supprimer_sa_reponse_de_suivi(self):
        """
        Un·e RESPONDER ne peut pas supprimer sa propre réponse de suivi — reçoit un 403
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        parent = ResponseFactory(survey=survey)
        suivi_reponse = ResponseFactory(
            survey=None,
            survey_follow_up=follow_up,
            parent_response=parent,
            respondant=authenticate.user,
        )
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.delete(response_url(suivi_reponse.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_autre_org_ne_peut_pas_supprimer_une_reponse_de_suivi(self):
        """
        Un·e ADMIN d'une autre organisation ne peut pas supprimer la réponse de suivi — reçoit un 404
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        suivi_reponse, _ = self._make_follow_up_response(org)
        MembershipFactory(user=authenticate.user, organisation=autre_org, membership_type=MembershipType.ADMIN)

        response = self.client.delete(response_url(suivi_reponse.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_pole_peut_supprimer_une_reponse_de_suivi_de_son_pole(self):
        """
        Un·e ADMIN de pôle peut supprimer une réponse de suivi rattachée à son pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        suivi_reponse, _ = self._make_follow_up_response(org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.delete(response_url(suivi_reponse.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @authenticate
    def test_admin_pole_ne_peut_pas_supprimer_une_reponse_de_suivi_dun_autre_pole(self):
        """
        Un·e ADMIN de pôle ne peut pas supprimer une réponse de suivi d'un autre pôle — reçoit un 404
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        suivi_reponse, _ = self._make_follow_up_response(org, pole=autre_pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.delete(response_url(suivi_reponse.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_suppression_reponse_de_suivi_est_un_soft_delete(self):
        """
        La suppression d'une réponse de suivi est un soft-delete :
        l'enregistrement reste en base avec is_active=False
        """
        org = OrganisationFactory()
        suivi_reponse, _ = self._make_follow_up_response(org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        self.client.delete(response_url(suivi_reponse.id))

        self.assertTrue(Response.objects.filter(pk=suivi_reponse.pk).exists())
        suivi_reponse.refresh_from_db()
        self.assertFalse(suivi_reponse.is_active)


class TestDeleteResponseEdgeCases(APITestCase):
    @authenticate
    def test_suppression_reponse_sans_survey_ni_follow_up_retourne_403(self):
        """
        Supprimer une réponse dont survey et survey_follow_up sont tous les deux null
        retourne un 403 plutôt qu'un crash HTTP 500.
        La réponse est visible via le rôle RESPONDER (respondant = user), mais
        CanDeleteResponse ne peut pas déterminer l'organisation → refuse l'accès.
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        orphan = ResponseFactory(survey=None, survey_follow_up=None, respondant=authenticate.user)

        response = self.client.delete(response_url(orphan.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
