from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory, VocabularyEntryFactory, VocabularySetFactory
from surveys.models import VocabularyCategory


def _org_with_forest(user):
    """Crée une organisation ayant accès à la catégorie forêt, avec l'utilisateur comme RESPONDER."""
    org = OrganisationFactory(vocabulary_categories=[VocabularyCategory.FOREST])
    MembershipFactory(user=user, organisation=org, membership_type=MembershipType.RESPONDER)
    return org


class TestVocabularySetList(APITestCase):
    def test_unauthenticated_cannot_list_vocabularies(self):
        """
        Un utilisateur non authentifié ne peut pas lister les vocabulaires
        """
        response = self.client.get(reverse("vocabulary_set_list"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_user_without_membership_sees_nothing(self):
        """
        Un utilisateur sans rôle ne voit aucun vocabulaire — l'accès est basé sur les catégories de l'organisation
        """
        VocabularySetFactory()

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_member_sees_vocabularies_of_accessible_categories(self):
        """
        Un membre d'organisation voit les vocabulaires dont la catégorie est accessible à son organisation
        """
        _org_with_forest(authenticate.user)
        visible = VocabularySetFactory(category=VocabularyCategory.FOREST)
        VocabularySetFactory(category="other")

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()]
        self.assertIn(visible.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_member_cannot_see_vocabularies_of_inaccessible_categories(self):
        """
        Un membre ne voit pas les vocabulaires d'une catégorie à laquelle son organisation n'a pas accès
        """
        OrganisationFactory()
        MembershipFactory(
            user=authenticate.user, organisation=OrganisationFactory(), membership_type=MembershipType.RESPONDER
        )
        VocabularySetFactory(category=VocabularyCategory.FOREST)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_response_shape(self):
        """
        La liste retourne uniquement id, code et name — sans les entrées
        """
        _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        VocabularyEntryFactory(vocabulary_set=vocab)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["id"] == vocab.id)
        self.assertIn("id", vocab_data)
        self.assertIn("code", vocab_data)
        self.assertIn("name", vocab_data)
        self.assertNotIn("entries", vocab_data)

    @authenticate
    def test_inactive_vocabulary_set_excluded_from_list(self):
        """
        Un VocabularySet inactif n'apparaît pas dans la liste, même si sa catégorie est accessible
        """
        _org_with_forest(authenticate.user)
        active = VocabularySetFactory(category=VocabularyCategory.FOREST, is_active=True)
        VocabularySetFactory(category=VocabularyCategory.FOREST, is_active=False)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()]
        self.assertIn(active.id, ids)
        self.assertEqual(len(ids), 1)


class TestVocabularySetDetail(APITestCase):
    def test_unauthenticated_cannot_access_detail(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory()
        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_vocabulary_with_entries(self):
        """
        Le détail d'un vocabulaire accessible contient ses entrées actives
        """
        _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        active = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True)
        VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_codes = [e["code"] for e in response.json()["entries"]]
        self.assertIn(active.code, entry_codes)
        self.assertEqual(len(entry_codes), 1)

    @authenticate
    def test_member_can_access_vocabulary_of_org_category(self):
        """
        Un membre peut accéder au détail d'un vocabulaire dont la catégorie est accessible à son organisation
        """
        _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["code"], vocab.code)

    @authenticate
    def test_cannot_access_vocabulary_of_inaccessible_category(self):
        """
        Un membre ne peut pas accéder au vocabulaire d'une catégorie inaccessible — 404
        """
        MembershipFactory(
            user=authenticate.user, organisation=OrganisationFactory(), membership_type=MembershipType.ADMIN
        )
        other_vocab = VocabularySetFactory(category=VocabularyCategory.FOREST, code="ZZZZ")

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": other_vocab.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_response_shape(self):
        """
        Le détail contient id, code, name et entries avec code, label, position
        """
        _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
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

    @authenticate
    def test_inactive_vocabulary_set_returns_404(self):
        """
        Un VocabularySet inactif renvoie une 404, même si sa catégorie est accessible
        """
        _org_with_forest(authenticate.user)
        inactive = VocabularySetFactory(category=VocabularyCategory.FOREST, is_active=False)

        response = self.client.get(reverse("vocabulary_set_detail", kwargs={"code": inactive.code}), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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
        org = _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = [v["code"] for v in response.json()]
        self.assertIn(vocab.code, codes)

    @authenticate
    def test_returns_vocabularies_referenced_in_user_pole_role_surveys(self):
        """
        Un·e utilisateur·ice ayant un rôle de réponse pour un pôle peut voir les vocabulaires
        référencés dans les enquêtes sans pôle
        """
        pole = PoleFactory()
        org = pole.organisation
        org.vocabulary_categories = [VocabularyCategory.FOREST]
        org.save()
        MembershipFactory(
            user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.RESPONDER
        )
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
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
        org = _org_with_forest(authenticate.user)
        used_vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        unused_vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
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
        _org_with_forest(authenticate.user)
        other_org = OrganisationFactory()
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        SurveyFactory(organisation=other_org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_inactive_vocabulary_set_excluded_from_mobile_list(self):
        """
        Un VocabularySet inactif référencé dans une enquête n'est pas retourné dans la liste mobile
        """
        org = _org_with_forest(authenticate.user)
        inactive_vocab = VocabularySetFactory(category=VocabularyCategory.FOREST, is_active=False)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(inactive_vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_non_responder_gets_empty_list(self):
        """
        Un·e ADMIN sans rôle RESPONDER obtient une liste vide
        """
        org = OrganisationFactory(vocabulary_categories=[VocabularyCategory.FOREST])
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    @authenticate
    def test_response_includes_entries(self):
        """
        Les entrées actives sont incluses dans la réponse mobile
        """
        org = _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(category=VocabularyCategory.FOREST)
        active = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True)
        VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)
        SurveyFactory(organisation=org, json_schema=self._schema_with_vocabulary(vocab.code))

        response = self.client.get(reverse("mobile_vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json() if v["code"] == vocab.code)
        entry_codes = [e["code"] for e in vocab_data["entries"]]
        self.assertIn(active.code, entry_codes)
        self.assertEqual(len(entry_codes), 1)
