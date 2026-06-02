from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory, VocabularyEntryFactory, VocabularySetFactory


class TestVocabularySetList(APITestCase):
    def test_unauthenticated_cannot_list_vocabularies(self):
        """
        Un utilisateur non authentifié ne peut pas lister les vocabulaires
        """
        response = self.client.get(reverse("vocabulary_set_list"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_shared_vocabularies_without_membership(self):
        """
        Un utilisateur sans rôle voit uniquement les vocabulaires partagés (sans organisation)
        """
        shared = VocabularySetFactory(organisation=None)
        org = OrganisationFactory()
        VocabularySetFactory(organisation=org)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()]
        self.assertIn(shared.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_member_sees_org_and_shared_vocabularies(self):
        """
        Un membre d'organisation voit les vocabulaires de son organisation et les partagés
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        org_vocab = VocabularySetFactory(organisation=org)
        shared_vocab = VocabularySetFactory(organisation=None)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()]
        self.assertIn(org_vocab.id, ids)
        self.assertIn(shared_vocab.id, ids)

    @authenticate
    def test_member_cannot_see_other_org_vocabularies(self):
        """
        Un membre ne voit pas les vocabulaires d'une autre organisation
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        VocabularySetFactory(organisation=other_org)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_response_shape(self):
        """
        La liste retourne uniquement id, code et name — sans les entrées
        """
        vocab = VocabularySetFactory(organisation=None)
        VocabularyEntryFactory(vocabulary_set=vocab)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["id"] == vocab.id)
        self.assertIn("id", vocab_data)
        self.assertIn("code", vocab_data)
        self.assertIn("name", vocab_data)
        self.assertNotIn("entries", vocab_data)


class TestVocabularySetDetail(APITestCase):
    def test_unauthenticated_cannot_access_detail(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=None)
        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_vocabulary_with_entries(self):
        """
        Le détail d'un vocabulaire accessible contient ses entrées actives
        """
        vocab = VocabularySetFactory(organisation=None)
        active = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True)
        VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_codes = [e["code"] for e in response.json()["entries"]]
        self.assertIn(active.code, entry_codes)
        self.assertEqual(len(entry_codes), 1)

    @authenticate
    def test_org_member_can_access_org_vocabulary(self):
        """
        Un membre peut accéder au détail d'un vocabulaire de son organisation
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        vocab = VocabularySetFactory(organisation=org)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["code"], vocab.code)

    @authenticate
    def test_cannot_access_other_org_vocabulary(self):
        """
        Un membre ne peut pas accéder au vocabulaire d'une autre organisation — 404
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        other_vocab = VocabularySetFactory(organisation=other_org, code="ZZZZ")

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": other_vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_response_shape(self):
        """
        Le détail contient id, code, name et entries avec code, label, position
        """
        vocab = VocabularySetFactory(organisation=None)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True, position=1)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("code", data)
        self.assertIn("name", data)
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 1)
        entry_data = data["entries"][0]
        self.assertEqual(entry_data["code"], entry.code)
        self.assertEqual(entry_data["label"], entry.label)
        self.assertEqual(entry_data["position"], entry.position)


class TestMobileVocabularySetList(APITestCase):
    def _schema_with_vocabulary(self, code):
        return {"fields": [{"id": "field_1", "type": "string", "vocabulary": code}]}

    def test_unauthenticated_cannot_list(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_only_vocabularies_referenced_in_user_surveys(self):
        """
        Seuls les vocabulaires référencés dans les enquêtes accessibles sont retournés
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        vocab = VocabularySetFactory(organisation=None)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [v["code"] for v in response.json()]
        self.assertIn(vocab.code, codes)

    @authenticate
    def test_excludes_vocabularies_not_referenced_in_user_surveys(self):
        """
        Un vocabulaire non utilisé dans les enquêtes n'est pas retourné
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        used_vocab = VocabularySetFactory(organisation=None)
        unused_vocab = VocabularySetFactory(organisation=None)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(used_vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [v["code"] for v in response.json()]
        self.assertIn(used_vocab.code, codes)
        self.assertNotIn(unused_vocab.code, codes)

    @authenticate
    def test_excludes_surveys_from_other_orgs(self):
        """
        Les vocabulaires des enquêtes d'autres organisations ne sont pas retournés
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        vocab = VocabularySetFactory(organisation=None)
        SurveyFactory(organisation=other_org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_non_responder_gets_empty_list(self):
        """
        Un MANAGER ou ADMIN sans rôle RESPONDER obtient une liste vide
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.MANAGER)
        vocab = VocabularySetFactory(organisation=None)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_response_includes_entries(self):
        """
        Les entrées actives sont incluses dans la réponse mobile
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        vocab = VocabularySetFactory(organisation=None)
        active = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True)
        VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["code"] == vocab.code)
        entry_codes = [e["code"] for e in vocab_data["entries"]]
        self.assertIn(active.code, entry_codes)
        self.assertEqual(len(entry_codes), 1)
