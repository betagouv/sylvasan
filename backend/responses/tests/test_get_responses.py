from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory

from responses.factories import ResponseFactory


class TestGetResponses(APITestCase):
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
        self.assertEqual(response.json(), [])

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
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey_response.id)

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
        self.assertEqual(len(response.json()), 0)

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
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey_response.id)

    # Role MANAGER

    @authenticate
    def test_org_manager_sees_all_responses_in_org(self):
        """
        Un·e MANAGER au niveau organisation voit toutes les réponses de cette organisation,
        y compris celles créées par d'autres utilisateur·ices
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        survey_response_a = ResponseFactory(survey=survey)
        survey_response_b = ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()]
        self.assertIn(survey_response_a.id, ids)
        self.assertIn(survey_response_b.id, ids)

    @authenticate
    def test_org_manager_sees_responses_for_pole_surveys(self):
        """
        Un·e MANAGER au niveau organisation voit aussi les réponses des enquêtes rattachées
        à des pôles de cette organisation
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()

        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey_response.id)

    @authenticate
    def test_org_manager_cannot_see_responses_from_other_org(self):
        """
        Un·e MANAGER ne voit pas les réponses d'une autre organisation
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        ResponseFactory(survey=SurveyFactory(organisation=other_org))

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    @authenticate
    def test_pole_manager_sees_responses_for_their_pole(self):
        """
        Un·e MANAGER de pôle voit les réponses des enquêtes de ce pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        survey_response = ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]["id"], survey_response.id)

    @authenticate
    def test_pole_manager_cannot_see_responses_from_other_pole(self):
        """
        Un·e MANAGER de pôle ne voit pas les réponses des enquêtes d'un autre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        other_pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        ResponseFactory(survey=SurveyFactory(organisation=org, pole=other_pole))

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    @authenticate
    def test_pole_manager_cannot_see_org_level_responses(self):
        """
        Un·e MANAGER de pôle ne voit pas les réponses des enquêtes sans pôle (niveau organisation)
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.MANAGER)
        ResponseFactory(survey=SurveyFactory(organisation=org, pole=None))

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

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
        ids = [r["id"] for r in response.json()]
        self.assertIn(survey_response_a.id, ids)
        self.assertIn(survey_response_b.id, ids)

    # Plusieurs rôles

    @authenticate
    def test_multiple_memberships_aggregate_responses(self):
        """
        Un·e utilisateur·ice avec plusieurs rôles voit l'agrégat des réponses
        auxquelles chaque rôle lui donne accès :
        - RESPONDER dans org A → ses propres réponses uniquement
        - MANAGER dans org B → toutes les réponses de org B
        """
        org_a = OrganisationFactory()
        org_b = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org_a, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org_b, membership_type=MembershipType.MANAGER)

        ma_survey_response_org_a = ResponseFactory(
            survey=SurveyFactory(organisation=org_a), respondant=authenticate.user
        )
        survey_response_autre_org_a = ResponseFactory(survey=SurveyFactory(organisation=org_a))
        survey_response_org_b = ResponseFactory(survey=SurveyFactory(organisation=org_b))

        response = self.client.get(reverse("response_list_create"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()]

        # Visible : sa propre réponse dans org A et toutes les réponses de org B
        self.assertIn(ma_survey_response_org_a.id, ids)
        self.assertIn(survey_response_org_b.id, ids)

        # Non visible : la réponse d'un·e autre dans org A (rôle RESPONDER uniquement)
        self.assertNotIn(survey_response_autre_org_a.id, ids)


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
    def test_manager_gets_empty_list(self):
        """
        Un·e MANAGER sans rôle RESPONDER ne voit aucune réponse
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=authenticate.user)

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
    def test_user_with_both_responder_and_manager_roles_sees_only_own_responses(self):
        """
        Un·e utilisateur·ice avec les rôles RESPONDER et MANAGER ne voit que ses propres réponses
        (pas toutes les réponses de l'organisation comme le ferait le rôle MANAGER)
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        own_response = ResponseFactory(survey=SurveyFactory(organisation=org), respondant=authenticate.user)
        other_response = ResponseFactory(survey=SurveyFactory(organisation=org))

        response = self.client.get(reverse("response_responder_retrieve"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()]
        self.assertIn(own_response.id, ids)
        # Les réponses des autres ne sont pas visibles, même si MANAGER dans la même org
        self.assertNotIn(other_response.id, ids)
