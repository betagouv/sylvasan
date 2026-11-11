import io

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


def _bulk_import_url(vocabularyset_pk):
    return reverse("vocabulary_entry_bulk_import", kwargs={"vocabularyset_pk": vocabularyset_pk})


def _csv(content: str):
    """Construit un fichier CSV UTF-8 simulé à partir d'une chaîne."""
    f = io.BytesIO(content.encode("utf-8"))
    f.name = "entries.csv"
    return f


class TestBulkImport(APITestCase):
    def test_unauthenticated_gets_401(self):
        """
        Un utilisateur non authentifié reçoit une 401
        """
        vocab = VocabularySetFactory(organisation=OrganisationFactory())
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": _csv("a,b"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_gets_403(self):
        """
        Un RESPONDER reçoit une 403
        """
        org = _org_with_responder(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": _csv("a,b"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_of_other_org_gets_404(self):
        """
        Un admin d'une autre organisation reçoit une 404
        """
        _org_with_admin(authenticate.user)
        other_vocab = VocabularySetFactory(organisation=OrganisationFactory())
        response = self.client.post(_bulk_import_url(other_vocab.pk), {"file": _csv("a,b"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_inactive_vocabularyset_gets_404(self):
        """
        Un référentiel inactif renvoie une 404
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org, is_active=False)
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": _csv("a,b"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_missing_file_returns_400(self):
        """
        L'absence de fichier renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(_bulk_import_url(vocab.pk), {"dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_bad_encoding_returns_400(self):
        """
        Un fichier non encodé en UTF-8 renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        f = io.BytesIO("code,libellé\na,Éléphant".encode("latin-1"))
        f.name = "entries.csv"
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": f, "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_empty_csv_returns_400(self):
        """
        Un fichier CSV vide (ou ne contenant que des lignes vides) renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": _csv("\n\n"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_too_few_columns_returns_400(self):
        """
        Un CSV avec moins de 2 colonnes renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk), {"file": _csv("code_seulement\na\n"), "dry_run": "true"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_too_many_columns_returns_400(self):
        """
        Un CSV avec plus de 3 colonnes renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(_bulk_import_url(vocab.pk), {"file": _csv("a,b,c,d\n"), "dry_run": "true"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_invalid_position_returns_400(self):
        """
        Une valeur non entière dans la colonne position renvoie une 400
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha,pas-un-nombre\n"), "dry_run": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Mode simulation (dry run) ---

    @authenticate
    def test_dry_run_returns_200_and_does_not_create(self):
        """
        En mode dry_run, la réponse est 200 et aucune entrée n'est créée en base
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha\nB02,Beta\n"), "dry_run": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(VocabularyEntry.objects.filter(vocabulary_set=vocab).exists())

    @authenticate
    def test_dry_run_response_contains_expected_entries(self):
        """
        Le dry run retourne les entrées du CSV avec leur code, label et position
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha,1\nB02,Beta,2\n"), "dry_run": "true"},
        )
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["code"], "A01")
        self.assertEqual(data[0]["label"], "Alpha")
        self.assertEqual(data[0]["position"], 1)
        self.assertEqual(data[1]["code"], "B02")

    @authenticate
    def test_import_creates_entries_and_returns_201(self):
        """
        Un import réel crée les entrées en base et renvoie une 201
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha\nB02,Beta\n"), "dry_run": "false"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VocabularyEntry.objects.filter(vocabulary_set=vocab).count(), 2)

    @authenticate
    def test_import_stores_position(self):
        """
        La position est correctement enregistrée depuis la 3e colonne
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha,5\n"), "dry_run": "false"},
        )
        entry = VocabularyEntry.objects.get(vocabulary_set=vocab, code="A01")
        self.assertEqual(entry.position, 5)

    @authenticate
    def test_import_upserts_existing_entry(self):
        """
        Une entrée existante (même code) est mise à jour plutôt que dupliquée
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        VocabularyEntryFactory(vocabulary_set=vocab, code="A01", label="Ancien label")

        self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Nouveau label\n"), "dry_run": "false"},
        )

        self.assertEqual(VocabularyEntry.objects.filter(vocabulary_set=vocab, code="A01").count(), 1)
        self.assertEqual(VocabularyEntry.objects.get(vocabulary_set=vocab, code="A01").label, "Nouveau label")

    @authenticate
    def test_import_reactivates_inactive_entry(self):
        """
        Une entrée préalablement désactivée est réactivée lors de l'import
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        VocabularyEntryFactory(vocabulary_set=vocab, code="A01", is_active=False)

        self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01,Alpha\n"), "dry_run": "false"},
        )

        entry = VocabularyEntry.objects.get(vocabulary_set=vocab, code="A01")
        self.assertTrue(entry.is_active)

    @authenticate
    def test_import_semicolon_delimited_csv(self):
        """
        Un CSV séparé par des points-virgules est correctement importé
        """
        org = _org_with_admin(authenticate.user)
        vocab = VocabularySetFactory(organisation=org)
        response = self.client.post(
            _bulk_import_url(vocab.pk),
            {"file": _csv("A01;Alpha;1\nB02;Beta;2\n"), "dry_run": "false"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VocabularyEntry.objects.filter(vocabulary_set=vocab).count(), 2)
        self.assertEqual(VocabularyEntry.objects.get(vocabulary_set=vocab, code="A01").label, "Alpha")
