from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase

from surveys.factories import VocabularyEntryFactory, VocabularySetFactory
from surveys.models import VocabularyEntry


def _create_url(vocabularyset_pk):
    return reverse(
        "vocabulary_entry_admin_create_view",
        kwargs={"vocabularyset_pk": vocabularyset_pk},
    )


def _url(vocabularyset_pk, entry_pk):
    return reverse(
        "vocabulary_entry_admin_view",
        kwargs={"vocabularyset_pk": vocabularyset_pk, "pk": entry_pk},
    )


def _org_with_admin(user):
    """Crée une organisation avec l'utilisateur comme ADMIN."""
    org = OrganisationFactory()
    MembershipFactory(user=user, organisation=org, membership_type=MembershipType.ADMIN)
    return org


def _org_with_responder(user):
    """Crée une organisation avec l'utilisateur comme RESPONDER."""
    org = OrganisationFactory()
    MembershipFactory(user=user, organisation=org, membership_type=MembershipType.RESPONDER)
    return org


class TestVocabularyEntryAdminViewRetrieve(APITestCase):
    def test_unauthenticated_cannot_access(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=OrganisationFactory())
        entry = VocabularyEntryFactory(vocabulary_set=vocab)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_gets_403(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER reçoit une 403
        """
        org = _org_with_responder(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_can_retrieve_entry(self):
        """
        Un admin peut accéder au détail d'une entrée de son organisation
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], entry.id)

    @authenticate
    def test_admin_cannot_access_entry_of_other_org(self):
        """
        Un admin ne peut pas accéder à une entrée d'un référentiel d'une autre organisation — 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())
        entry = VocabularyEntryFactory(vocabulary_set=other_vocab)
        response = self.client.get(_url(other_vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_cannot_access_entry_of_inactive_vocabularyset(self):
        """
        Un admin ne peut pas accéder à une entrée d'un référentiel inactif — 404
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org, is_active=False)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_admin_cannot_access_inactive_entry(self):
        """
        Une entrée inactive renvoie une 404
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, is_active=False)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_response_shape(self):
        """
        La réponse contient id, code, label et position
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, position=3)
        response = self.client.get(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("code", data)
        self.assertIn("label", data)
        self.assertIn("position", data)
        self.assertEqual(data["position"], 3)


class TestVocabularyEntryAdminViewUpdate(APITestCase):
    @authenticate
    def test_admin_can_update_entry(self):
        """
        Un admin peut modifier le label et la position d'une entrée
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, label="Ancien label", position=1)

        response = self.client.patch(
            _url(vocab.pk, entry.pk),
            {"label": "Nouveau label", "position": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry.refresh_from_db()
        self.assertEqual(entry.label, "Nouveau label")
        self.assertEqual(entry.position, 5)

    @authenticate
    def test_responder_cannot_update(self):
        """
        Un RESPONDER ne peut pas modifier une entrée — 403
        """
        org = _org_with_responder(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab, label="Original")

        response = self.client.patch(_url(vocab.pk, entry.pk), {"label": "Modifié"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        entry.refresh_from_db()
        self.assertEqual(entry.label, "Original")

    @authenticate
    def test_admin_cannot_update_entry_of_other_org(self):
        """
        Un admin ne peut pas modifier une entrée d'un référentiel d'une autre organisation — 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())
        entry = VocabularyEntryFactory(vocabulary_set=other_vocab, label="Original")

        response = self.client.patch(_url(other_vocab.pk, entry.pk), {"label": "Modifié"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        entry.refresh_from_db()
        self.assertEqual(entry.label, "Original")


class TestVocabularyEntryAdminViewDelete(APITestCase):
    def test_unauthenticated_cannot_delete(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=OrganisationFactory())
        entry = VocabularyEntryFactory(vocabulary_set=vocab)
        response = self.client.delete(_url(vocab.pk, entry.pk), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_admin_can_delete_entry(self):
        """
        Un admin peut supprimer (désactiver) une entrée — 204
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)

        response = self.client.delete(_url(vocab.pk, entry.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        entry.refresh_from_db()
        self.assertFalse(entry.is_active)

    @authenticate
    def test_delete_is_soft(self):
        """
        La suppression ne détruit pas la ligne en base — elle la marque inactive
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)

        self.client.delete(_url(vocab.pk, entry.pk), format="json")

        from surveys.models import VocabularyEntry

        self.assertTrue(VocabularyEntry.objects.filter(pk=entry.pk).exists())

    @authenticate
    def test_responder_cannot_delete(self):
        """
        Un RESPONDER ne peut pas supprimer une entrée — 403
        """
        org = _org_with_responder(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        entry = VocabularyEntryFactory(vocabulary_set=vocab)

        response = self.client.delete(_url(vocab.pk, entry.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        entry.refresh_from_db()
        self.assertTrue(entry.is_active)

    @authenticate
    def test_admin_cannot_delete_entry_of_other_org(self):
        """
        Un admin ne peut pas supprimer une entrée d'un référentiel d'une autre organisation — 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())
        entry = VocabularyEntryFactory(vocabulary_set=other_vocab)

        response = self.client.delete(_url(other_vocab.pk, entry.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        entry.refresh_from_db()
        self.assertTrue(entry.is_active)


class TestVocabularyEntryAdminCreateView(APITestCase):
    def test_unauthenticated_cannot_create(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=OrganisationFactory())
        response = self.client.post(
            _create_url(vocab.pk),
            {"code": "A", "label": "Alpha"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_gets_403(self):
        """
        Un utilisateur avec uniquement un rôle RESPONDER reçoit une 403
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _create_url(vocab.pk),
            {"code": "A", "label": "Alpha"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_can_create_entry(self):
        """
        Un admin peut créer une entrée dans un référentiel de son organisation — 201
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        vocab = VocabularySetFactory(organisation=org)

        response = self.client.post(
            _create_url(vocab.pk),
            {"code": "NEW", "label": "Nouvelle entrée", "position": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["code"], "NEW")
        self.assertEqual(data["label"], "Nouvelle entrée")
        self.assertEqual(data["position"], 5)

    @authenticate
    def test_created_entry_is_linked_to_vocabulary_set(self):
        """
        L'entrée créée est bien rattachée au référentiel indiqué dans l'URL
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        vocab = VocabularySetFactory(organisation=org)

        self.client.post(
            _create_url(vocab.pk),
            {"code": "X", "label": "Entrée X"},
            format="json",
        )

        self.assertTrue(VocabularyEntry.objects.filter(vocabulary_set=vocab, code="X").exists())

    @authenticate
    def test_admin_cannot_create_entry_in_other_org_vocabulary(self):
        """
        Un admin ne peut pas créer une entrée dans un référentiel d'une autre organisation — 404
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())

        response = self.client.post(
            _create_url(other_vocab.pk),
            {"code": "A", "label": "Alpha"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(VocabularyEntry.objects.filter(vocabulary_set=other_vocab).exists())

    @authenticate
    def test_admin_cannot_create_entry_in_inactive_vocabulary(self):
        """
        Un admin ne peut pas créer une entrée dans un référentiel inactif — 404
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        vocab = VocabularySetFactory(organisation=org, is_active=False)

        response = self.client.post(
            _create_url(vocab.pk),
            {"code": "A", "label": "Alpha"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_missing_required_fields_returns_400(self):
        """
        Les champs obligatoires manquants renvoient une 400
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        vocab = VocabularySetFactory(organisation=org)

        response = self.client.post(_create_url(vocab.pk), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
