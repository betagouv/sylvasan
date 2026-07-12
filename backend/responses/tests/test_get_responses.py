from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory

from responses.factories import ResponseFactory


class TestGetResponses(APITestCase):
    def get_results(self, response):
        return response.json()["results"]

    def test_unauthenticated_cannot_list_responses(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        response = self.client.get(reverse("response_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_returns_empty_list(self):
        """
        Un·e utilisateur·ice authentifié·e sans rôle ne voit aucune réponse
        """
        ResponseFactory()
        response = self.client.get(reverse("response_list_create"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_results(response), [])

    @authenticate
    def test_responder_sees_their_own_responses(self):
        """
        Un·e RESPONDER voit les réponses qu'il ou elle a créées
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        survey_response = ResponseFactory(survey=survey, respondant=authenticate.user)

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], survey_response.id)

    @authenticate
    def test_responder_cannot_see_other_users_responses(self):
        """
        Un·e RESPONDER ne voit pas les réponses d'un·e autre utilisateur·ice à la même enquête
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        ResponseFactory(survey=survey)  # répondant différent

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.get_results(response)), 0)

    @authenticate
    def test_responder_cannot_see_responses_from_other_org(self):
        """
        Un·e RESPONDER voit les réponses d'une organisation dont il ou elle ne fait pas partie,
        seulement si ces réponses lui sont attribuées
        """
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        survey_response = ResponseFactory(
            survey=SurveyFactory(organisation=autre_org),
            respondant=authenticate.user,
        )

        response = self.client.get(reverse("response_list_create"), format="json")

        # La réponse appartient bien à l'utilisateur, même si la personne n'a plus le role dans cet
        # organisation, la réponse est renvoyée.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], survey_response.id)

    # Role ADMIN

    @authenticate
    def test_org_admin_sees_all_responses_in_org(self):
        """
        Un·e ADMIN au niveau organisation voit toutes les réponses de cette organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey_response_a = ResponseFactory(survey=survey)
        survey_response_b = ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in self.get_results(response)]
        self.assertIn(survey_response_a.id, ids)
        self.assertIn(survey_response_b.id, ids)

    # Plusieurs rôles

    @authenticate
    def test_multiple_memberships_aggregate_responses(self):
        """
        Un·e utilisateur·ice avec plusieurs rôles voit l'agrégat des réponses
        auxquelles chaque rôle lui donne accès :
        - RESPONDER dans org A → ses propres réponses uniquement
        - ADMIN dans org B → toutes les réponses de org B
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.ADMIN)

        ma_survey_response_org_a = ResponseFactory(
            survey=SurveyFactory(organisation=org_a), respondant=authenticate.user
        )
        survey_response_autre_org_a = ResponseFactory(survey=SurveyFactory(organisation=org_a))
        survey_response_org_b = ResponseFactory(survey=SurveyFactory(organisation=org_b))

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in self.get_results(response)]

        # Visible : sa propre réponse dans org A et toutes les réponses de org B
        self.assertIn(ma_survey_response_org_a.id, ids)
        self.assertIn(survey_response_org_b.id, ids)

        # Non visible : la réponse d'un·e autre dans org A (rôle RESPONDER uniquement)
        self.assertNotIn(survey_response_autre_org_a.id, ids)

    @authenticate
    def test_admin_pole_voit_les_reponses_au_suivi_niveau_org(self):
        """
        Un·e ADMIN de pôle voit les réponses aux suivis rattachés à l'organisation (pole=None),
        et pas seulement ceux rattachés à son propre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org)
        follow_up_org = SurveyFollowUpFactory(organisation=org, pole=None, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)
        parent = ResponseFactory(survey=survey)
        reponse_suivi_org = ResponseFactory(survey=None, survey_follow_up=follow_up_org, parent_response=parent)

        response = self.client.get(reverse("response_list_create"), {"include_follow_ups": "true"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in self.get_results(response)]
        self.assertIn(reponse_suivi_org.id, ids)


class TestResponseFullList(APITestCase):
    def test_unauthenticated_cannot_list_full_responses(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        response = self.client.get(reverse("response_responder_retrieve"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_no_membership_returns_empty_list(self):
        """
        Un·e utilisateur·ice sans rôle ne voit aucune réponse
        """
        ResponseFactory()
        response = self.client.get(reverse("response_responder_retrieve"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_responder_sees_their_own_responses(self):
        """
        Un·e RESPONDER voit ses propres réponses avec la représentation complète
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        own_response = ResponseFactory(survey=SurveyFactory(organisation=org), respondant=authenticate.user)

        response = self.client.get(reverse("response_responder_retrieve"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], own_response.id)

    @authenticate
    def test_responder_cannot_see_other_users_responses(self):
        """
        Un·e RESPONDER ne voit pas les réponses d'un·e autre utilisateur·ice
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        ResponseFactory(survey=SurveyFactory(organisation=org))  # répondant différent

        response = self.client.get(reverse("response_responder_retrieve"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    @authenticate
    def test_admin_gets_empty_list(self):
        """
        Un·e ADMIN sans rôle RESPONDER ne voit aucune réponse
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=authenticate.user)

        response = self.client.get(reverse("response_responder_retrieve"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    @authenticate
    def test_user_with_both_responder_and_admin_roles_sees_only_own_responses(self):
        """
        Un·e utilisateur·ice avec les rôles RESPONDER et ADMIN ne voit que ses propres réponses
        via l'endpoint responder (pas toutes les réponses de l'organisation)
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        own_response = ResponseFactory(survey=SurveyFactory(organisation=org), respondant=authenticate.user)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org))

        response = self.client.get(reverse("response_responder_retrieve"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()]
        self.assertIn(own_response.id, ids)
        self.assertNotIn(other_response.id, ids)


class TestInactiveResponsesExclues(APITestCase):
    @authenticate
    def test_reponse_inactive_non_retournee_dans_la_liste(self):
        """
        Une réponse désactivée (is_active=False) n'est pas retournée par l'endpoint de liste,
        même si l'utilisateur·ice a normalement accès à cette réponse
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        reponse_active = ResponseFactory(survey=survey)
        reponse_inactive = ResponseFactory(survey=survey)
        reponse_inactive.deactivate()

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()["results"]]
        self.assertIn(reponse_active.id, ids)
        self.assertNotIn(reponse_inactive.id, ids)


class TestFiltreIncludeFollowUps(APITestCase):
    """
    Vérifie que les réponses de suivi sont exclues par défaut et incluses
    uniquement si le paramètre include_follow_ups=true est fourni.
    """

    def get_ids(self, response):
        return [r["id"] for r in response.json()["results"]]

    def _setup_org_with_followup(self):
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        reponse_principale = ResponseFactory(survey=survey)
        reponse_suivi = ResponseFactory(survey=None, survey_follow_up=follow_up, parent_response=reponse_principale)
        return reponse_principale, reponse_suivi

    @authenticate
    def test_followups_exclus_par_defaut(self):
        """
        Sans paramètre include_follow_ups, les réponses de suivi ne sont pas retournées
        """
        reponse_principale, reponse_suivi = self._setup_org_with_followup()

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self.get_ids(response)
        self.assertIn(reponse_principale.id, ids)
        self.assertNotIn(reponse_suivi.id, ids)

    @authenticate
    def test_followups_exclus_si_parametre_false(self):
        """
        Avec include_follow_ups=false, les réponses de suivi sont exclues explicitement
        """
        reponse_principale, reponse_suivi = self._setup_org_with_followup()

        response = self.client.get(reverse("response_list_create"), {"include_follow_ups": "false"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self.get_ids(response)
        self.assertIn(reponse_principale.id, ids)
        self.assertNotIn(reponse_suivi.id, ids)

    @authenticate
    def test_followups_inclus_si_parametre_true(self):
        """
        Avec include_follow_ups=true, les réponses de suivi apparaissent dans la liste
        """
        reponse_principale, reponse_suivi = self._setup_org_with_followup()

        response = self.client.get(reverse("response_list_create"), {"include_follow_ups": "true"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self.get_ids(response)
        self.assertIn(reponse_principale.id, ids)
        self.assertIn(reponse_suivi.id, ids)

    @authenticate
    def test_reponses_de_premier_niveau_toujours_visibles(self):
        """
        Les réponses de premier niveau apparaissent quelle que soit la valeur du paramètre
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        reponse = ResponseFactory(survey=survey)

        for params in [{}, {"include_follow_ups": "false"}, {"include_follow_ups": "true"}]:
            with self.subTest(params=params):
                resp = self.client.get(reverse("response_list_create"), params, format="json")
                self.assertIn(reponse.id, self.get_ids(resp))


class TestRetrieveResponseWithFollowUps(APITestCase):
    @authenticate
    def test_follow_up_responses_inclus_dans_le_payload(self):
        """
        GET /api/responses/<pk>/ retourne les réponses de suivi dans follow_up_responses
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        parent = ResponseFactory(survey=survey)
        child = ResponseFactory(survey=None, survey_follow_up=follow_up, parent_response=parent)

        response = self.client.get(reverse("response_retrieve_destroy", kwargs={"pk": parent.id}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        follow_up_ids = [r["id"] for r in response.json()["followUpResponses"]]
        self.assertIn(child.id, follow_up_ids)


class TestFilterResponses(APITestCase):
    def get_ids(self, response):
        return [r["id"] for r in response.json()["results"]]

    @authenticate
    def test_filter_by_survey_returns_only_matching_responses(self):
        """
        Le paramètre ?survey=<id> ne retourne que les réponses de cette enquête,
        et exclut celles des autres enquêtes.
        """
        org = OrganisationFactory()
        survey_a = SurveyFactory(organisation=org)
        survey_b = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response_a = ResponseFactory(survey=survey_a)
        ResponseFactory(survey=survey_b)

        response = self.client.get(reverse("response_list_create"), {"survey": survey_a.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self.get_ids(response)
        self.assertEqual(ids, [response_a.id])
