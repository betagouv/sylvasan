from io import StringIO
from unittest.mock import MagicMock, patch

from django.test import TestCase

from organisations.models import Organisation
from surveys.models import VocabularyEntry, VocabularySet

from organisation_specific.dsf.management.commands.sync_dsf_vocabularies import Command


def _make_command():
    """Instancie la commande avec stdout/stderr/style mockés."""
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = MagicMock()
    cmd.style.SUCCESS = lambda x: x
    cmd.style.WARNING = lambda x: x
    cmd.style.ERROR = lambda x: x
    return cmd


def _mock_connections(rows):
    """Retourne un mock de connections['dsf_ref'] renvoyant *rows* depuis fetchall."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = rows
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connections = MagicMock()
    mock_connections.__getitem__.return_value = mock_conn
    return mock_connections


class SyncDsfVocabulariesCommandTest(TestCase):
    def setUp(self):
        self.dsf_org = Organisation.objects.create(name="DSF")

    @patch("organisation_specific.dsf.management.commands.sync_dsf_vocabularies.connections")
    def test_sync_vocabulary_reactivates_deactivated_set(self, mock_conns):
        """
        Un VocabularySet désactivé par la synchronisation API est réactivé
        lors d'une synchronisation DB classique (sans --api).
        """
        inactive = VocabularySet.objects.create(
            organisation=self.dsf_org, code="ESSDSF", name="Ancien nom", is_active=False
        )
        mock_conns.__getitem__ = _mock_connections([("OUL", "Orme à larges feuilles", 1)]).__getitem__

        cmd = _make_command()
        cmd._sync_vocabulary(
            self.dsf_org,
            {"code": "ESSDSF", "name": "Codification des essences DSF", "unite": "ESSDSF"},
            dry_run=False,
        )

        inactive.refresh_from_db()
        self.assertTrue(inactive.is_active)

    @patch("organisation_specific.dsf.management.commands.sync_dsf_vocabularies.connections")
    def test_sync_vocabulary_creates_entries(self, mock_conns):
        """
        _sync_vocabulary crée les VocabularyEntry renvoyées par metadsf.
        """
        mock_conns.__getitem__ = _mock_connections(
            [
                ("NON", "Non", 0),
                ("OUI", "Oui", 1),
            ]
        ).__getitem__

        cmd = _make_command()
        cmd._sync_vocabulary(
            self.dsf_org,
            {"code": "0/1", "name": "0/1", "unite": "0/1"},
            dry_run=False,
        )

        vocab = VocabularySet.objects.get(organisation=self.dsf_org, code="0/1")
        self.assertTrue(vocab.is_active)
        self.assertEqual(VocabularyEntry.objects.filter(vocabulary_set=vocab).count(), 2)

    @patch("organisation_specific.dsf.management.commands.sync_dsf_vocabularies.connections")
    def test_sync_vocabulary_deactivates_removed_entries(self, mock_conns):
        """
        Les entrées présentes en base mais absentes de metadsf sont désactivées.
        """
        vocab = VocabularySet.objects.create(organisation=self.dsf_org, code="0/1", name="0/1")
        VocabularyEntry.objects.create(vocabulary_set=vocab, code="OBSOLETE", label="Obsolète", is_active=True)

        mock_conns.__getitem__ = _mock_connections([("NON", "Non", 0)]).__getitem__

        cmd = _make_command()
        cmd._sync_vocabulary(
            self.dsf_org,
            {"code": "0/1", "name": "0/1", "unite": "0/1"},
            dry_run=False,
        )

        obsolete = VocabularyEntry.objects.get(vocabulary_set=vocab, code="OBSOLETE")
        self.assertFalse(obsolete.is_active)
