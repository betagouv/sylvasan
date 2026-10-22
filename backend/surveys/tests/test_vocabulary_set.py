from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import SurveyFactory, VocabularyEntryFactory, VocabularySetFactory
from surveys.models import VocabularyCategory


def _org_with_admin(user):
    """Crée une organisation avec l'utilisateur comme ADMIN."""
    org = OrganisationFactory()
    MembershipFactory(user=user, organisation=org, membership_type=MembershipType.ADMIN)
    return org


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
    def test_user_without_admin_role_gets_403(self):
        """
        Un utilisateur sans rôle admin reçoit une 403
        """
        VocabularySetFactory()

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_responder_only_gets_403(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER reçoit une 403
        """
        _org_with_forest(authenticate.user)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_sees_vocabularies_of_their_organisation(self):
        """
        Un admin voit les référentiels appartenant à son organisation
        """
        org = _org_with_admin(authenticate.user)
        visible = VocabularySetFactory(organisation=org)
        VocabularySetFactory(organisation=OrganisationFactory())

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()["results"]]
        self.assertIn(visible.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_admin_does_not_see_other_orgs_vocabularies(self):
        """
        Un admin ne voit pas les référentiels d'organisations qu'il n'administre pas
        """
        _org_with_admin(authenticate.user)
        VocabularySetFactory(organisation=OrganisationFactory())

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["results"], [])

    @authenticate
    def test_inactive_vocabulary_set_excluded_from_list(self):
        """
        Un VocabularySet inactif n'apparaît pas dans la liste admin
        """
        org = _org_with_admin(authenticate.user)
        active = VocabularySetFactory(organisation=org, is_active=True)
        VocabularySetFactory(organisation=org, is_active=False)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [v["id"] for v in response.json()["results"]]
        self.assertIn(active.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_response_is_paginated(self):
        """
        La réponse est paginée et contient count, results et organisations
        """
        org = _org_with_admin(authenticate.user)
        VocabularySetFactory(organisation=org)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIn("organisations", data)

    @authenticate
    def test_response_shape(self):
        """
        Chaque entrée de la liste contient id, code, name, organisation_name et entries
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        VocabularyEntryFactory(vocabulary_set=vocab)

        response = self.client.get(reverse("vocabulary_set_list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vocab_data = next(v for v in response.json()["results"] if v["id"] == vocab.id)
        self.assertIn("id", vocab_data)
        self.assertIn("code", vocab_data)
        self.assertIn("name", vocab_data)
        self.assertIn("organisationName", vocab_data)
        self.assertIn("entries", vocab_data)


class TestVocabularySetSearch(APITestCase):
    def setUp(self):
        self.user = None  # défini par @authenticate

    @authenticate
    def setUp_org(self):
        return _org_with_admin(authenticate.user)

    def _results(self, search):
        return self.client.get(reverse("vocabulary_set_list"), {"search": search}, format="json").json()["results"]

    @authenticate
    def test_search_by_code_returns_matching_vocab(self):
        """
        La recherche par code retourne le référentiel correspondant
        """
        org = _org_with_admin(authenticate.user)
        target = VocabularySetFactory(organisation=org, code="ESS2014", name="CODIFICATION DES ESSENCES")
        VocabularySetFactory(organisation=org, code="AUTRE", name="AUTRE REFERENTIEL")

        ids = [v["id"] for v in self._results("ESS2014")]

        self.assertIn(target.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_search_by_name_returns_matching_vocab(self):
        """
        La recherche par nom retourne le référentiel correspondant
        """
        org = _org_with_admin(authenticate.user)
        target = VocabularySetFactory(organisation=org, code="ESS2014", name="CODIFICATION DES ESSENCES")
        VocabularySetFactory(organisation=org, code="AUTRE", name="AUTRE REFERENTIEL")

        ids = [v["id"] for v in self._results("DES ESSENCES")]

        self.assertIn(target.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_search_by_partial_name_returns_matching_vocab(self):
        """
        La recherche par sous-chaîne du nom retourne le bon référentiel
        """
        org = _org_with_admin(authenticate.user)
        target = VocabularySetFactory(organisation=org, code="ESS2014", name="CODIFICATION DES ESSENCES")
        VocabularySetFactory(organisation=org, code="ZZZ", name="AUTRE REFERENTIEL")

        ids = [v["id"] for v in self._results("CODIFICATION")]

        self.assertIn(target.id, ids)
        self.assertEqual(len(ids), 1)

    @authenticate
    def test_search_with_no_match_returns_empty(self):
        """
        Une recherche sans correspondance retourne une liste vide
        """
        org = _org_with_admin(authenticate.user)
        VocabularySetFactory(organisation=org, code="ESS2014", name="CODIFICATION DES ESSENCES")

        ids = [v["id"] for v in self._results("INEXISTANT")]

        self.assertEqual(ids, [])

    @authenticate
    def test_search_does_not_return_other_org_results(self):
        """
        La recherche ne retourne pas les référentiels d'organisations non administrées
        """
        org = _org_with_admin(authenticate.user)
        VocabularySetFactory(organisation=org, code="ESS2014", name="CODIFICATION DES ESSENCES")
        VocabularySetFactory(organisation=OrganisationFactory(), code="ESS2015", name="CODIFICATION 2015")

        ids = [v["id"] for v in self._results("CODIFICATION")]

        self.assertEqual(len(ids), 1)


class TestVocabularySetRetrieveView(APITestCase):
    def test_unauthenticated_cannot_access(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=OrganisationFactory())
        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_gets_403(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER reçoit une 403
        """
        org = _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_can_access_own_org_vocabulary(self):
        """
        Un admin peut accéder au détail d'un référentiel de son organisation
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], vocab.id)

    @authenticate
    def test_admin_cannot_access_other_org_vocabulary(self):
        """
        Un admin ne peut pas accéder au référentiel d'une autre organisation — 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())
        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": other_vocab.pk}), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_inactive_vocabulary_returns_404(self):
        """
        Un VocabularySet inactif renvoie une 404, même pour un admin de l'organisation
        """
        org = _org_with_admin(authenticate.user)
        inactive = VocabularySetFactory(organisation=org, is_active=False)
        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": inactive.pk}), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_response_shape(self):
        """
        Le détail contient id, code, name, organisation_name et entries
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, is_active=True, position=1)

        response = self.client.get(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("code", data)
        self.assertIn("name", data)
        self.assertIn("organisationName", data)
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["code"], entry.code)

    @authenticate
    def test_admin_can_delete_own_org_vocabulary(self):
        """
        Un admin peut supprimer (désactiver) un référentiel de son organisation — 204
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)

        response = self.client.delete(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        vocab.refresh_from_db()
        self.assertFalse(vocab.is_active)

    @authenticate
    def test_delete_is_soft(self):
        """
        La suppression ne détruit pas la ligne en base — elle la marque inactive
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)

        self.client.delete(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")

        from surveys.models import VocabularySet

        self.assertTrue(VocabularySet.objects.filter(pk=vocab.pk).exists())

    @authenticate
    def test_responder_cannot_delete(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER ne peut pas supprimer — 403
        """
        org = _org_with_forest(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)

        response = self.client.delete(reverse("vocabulary_retrieve_view", kwargs={"pk": vocab.pk}), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        vocab.refresh_from_db()
        self.assertTrue(vocab.is_active)

    @authenticate
    def test_admin_cannot_delete_other_org_vocabulary(self):
        """
        Un admin ne peut pas supprimer le référentiel d'une autre organisation — 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())

        response = self.client.delete(
            reverse("vocabulary_retrieve_view", kwargs={"pk": other_vocab.pk}), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_vocab.refresh_from_db()
        self.assertTrue(other_vocab.is_active)


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


class TestVocabularySetCreate(APITestCase):
    def test_unauthenticated_cannot_create(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        org = OrganisationFactory()
        response = self.client.post(
            reverse("vocabulary_set_list"),
            {"code": "TST", "name": "Test", "organisation": org.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_cannot_create(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER reçoit une 403
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.post(
            reverse("vocabulary_set_list"),
            {"code": "TST", "name": "Test", "organisation": org.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_can_create_vocabulary_set(self):
        """
        Un admin peut créer un référentiel dans son organisation — 201
        """
        org = _org_with_admin(authenticate.user)
        response = self.client.post(
            reverse("vocabulary_set_list"),
            {"code": "NEW", "name": "Nouveau référentiel", "organisation": org.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["code"], "NEW")
        self.assertEqual(data["name"], "Nouveau référentiel")
        self.assertEqual(data["organisationName"], org.name)

    @authenticate
    def test_created_vocabulary_set_belongs_to_organisation(self):
        """
        Le référentiel créé est bien rattaché à l'organisation choisie
        """
        from surveys.models import VocabularySet

        org = _org_with_admin(authenticate.user)
        self.client.post(
            reverse("vocabulary_set_list"),
            {"code": "CHK", "name": "Vérification", "organisation": org.id},
            format="json",
        )
        self.assertTrue(VocabularySet.objects.filter(code="CHK", organisation=org).exists())

    @authenticate
    def test_admin_cannot_create_in_other_org(self):
        """
        Un admin ne peut pas créer un référentiel dans une organisation qu'il n'administre pas — 403
        """
        _org_with_admin(authenticate.user)
        other_org = OrganisationFactory()
        response = self.client.post(
            reverse("vocabulary_set_list"),
            {"code": "TST", "name": "Test", "organisation": other_org.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_missing_required_fields_returns_400(self):
        """
        Les champs obligatoires manquants renvoient une 400
        """
        _org_with_admin(authenticate.user)
        response = self.client.post(reverse("vocabulary_set_list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
