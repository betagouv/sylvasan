from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import VocabularyEntryFactory, VocabularySetFactory


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
    def test_inactive_entries_are_excluded(self):
        """
        Les entrées inactives d'un vocabulaire ne sont pas retournées
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        vocab = VocabularySetFactory(organisation=org)
        active_entry = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True)
        VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["id"] == vocab.id)
        entry_codes = [e["code"] for e in vocab_data["entries"]]
        self.assertIn(active_entry.code, entry_codes)
        self.assertEqual(len(entry_codes), 1)

    @authenticate
    def test_response_shape(self):
        """
        La réponse contient les champs attendus pour un vocabulaire et ses entrées
        """
        vocab = VocabularySetFactory(organisation=None)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, position=1)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["id"] == vocab.id)
        self.assertIn("id", vocab_data)
        self.assertIn("code", vocab_data)
        self.assertIn("name", vocab_data)
        self.assertIn("entries", vocab_data)
        self.assertEqual(len(vocab_data["entries"]), 1)
        entry_data = vocab_data["entries"][0]
        self.assertEqual(entry_data["code"], entry.code)
        self.assertEqual(entry_data["label"], entry.label)
        self.assertEqual(entry_data["position"], entry.position)
