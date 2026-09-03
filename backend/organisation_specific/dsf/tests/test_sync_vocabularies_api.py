import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

import requests
from organisations.models import Organisation
from surveys.models import VocabularyEntry, VocabularySet

from organisation_specific.dsf.sync_vocabularies_api import DSFApiError, sync_dsf_vocabularies_from_api

UNITES_RESPONSE = [
    # Unité CONTINU — doit être ignorée (on ne synchronise que les NOMINAL)
    {
        "unite": "%",
        "proprietaire": "IFN",
        "type": "CONTINU",
        "libelle": "%",
        "definition": "POURCENTAGE",
        "valmax": 100.0,
    },
    # Unité NOMINAL — doit être synchronisée
    {
        "unite": "0/1",
        "proprietaire": "DSF",
        "type": "NOMINAL",
        "libelle": "0/1",
        "definition": "CHIFFRE BOOLEEN",
        "valmax": None,
    },
    # Unité NOMINAL blacklistée — doit être ignorée
    {
        "unite": "CM",
        "proprietaire": "DSF",
        "type": "NOMINAL",
        "libelle": "Commune",
        "definition": "CODE COMMUNE",
        "valmax": None,
    },
]

MODES_COUNT_RESPONSE = {"count": 2}

MODES_RESPONSE = [
    {
        "unite": "0/1",
        "mode": "0",
        "position": 0,
        "classe": 1,
        "valeurint": None,
        "etendue": None,
        "hls": None,
        "rgb": None,
        "cmyk": None,
        "libelle": "NON",
        "definition": "FAUX",
    },
    {
        "unite": "0/1",
        "mode": "1",
        "position": 1,
        "classe": 1,
        "valeurint": None,
        "etendue": None,
        "hls": None,
        "rgb": None,
        "cmyk": None,
        "libelle": "OUI",
        "definition": "VRAI",
    },
    # Mode appartenant à une unité CONTINU — doit être ignoré lors du groupement
    {
        "unite": "%",
        "mode": "VAL",
        "position": 0,
        "classe": 0,
        "valeurint": None,
        "etendue": None,
        "hls": None,
        "rgb": None,
        "cmyk": None,
        "libelle": "Valeur",
        "definition": "VALEUR EN POURCENTAGE",
    },
]


def _make_response(status_code=200, json_data=None, content_type="application/json"):
    """Crée un mock de réponse requests avec les attributs nécessaires."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.headers = {"content-type": content_type}
    encoded = json.dumps(json_data).encode() if json_data is not None else b""
    mock.content = encoded
    if json_data is not None:
        mock.json.return_value = json_data
    else:
        mock.json.side_effect = ValueError("No JSON")
    return mock


def _standard_side_effect():
    """Séquence de réponses pour un appel nominal (3 requêtes)."""
    return [
        _make_response(json_data=UNITES_RESPONSE),  # GET /unites
        _make_response(json_data=MODES_COUNT_RESPONSE),  # GET /modes/count
        _make_response(json_data=MODES_RESPONSE),  # GET /modes
    ]


class SyncDsfVocabulariesApiTest(TestCase):
    def setUp(self):
        # L'organisation DSF doit exister pour que la synchronisation fonctionne
        self.dsf_org = Organisation.objects.create(name="DSF")

    # ------------------------------------------------------------------
    # Cas nominal
    # ------------------------------------------------------------------

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_happy_path_creates_sets_and_entries(self, mock_get):
        """
        Un appel nominal crée le VocabularySet et ses VocabularyEntry.
        """
        mock_get.side_effect = _standard_side_effect()

        result = sync_dsf_vocabularies_from_api()

        self.assertEqual(result["sets_created"], 1)
        self.assertEqual(result["entries_created"], 2)
        self.assertEqual(result["entries_updated"], 0)
        self.assertEqual(result["entries_deactivated"], 0)

        vocab = VocabularySet.objects.get(organisation=self.dsf_org, code="0/1")
        self.assertEqual(vocab.name, "0/1")

        entries = list(vocab.entries.order_by("position"))
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].code, "0")
        self.assertEqual(entries[0].label, "NON")
        self.assertEqual(entries[0].position, 0)
        self.assertEqual(entries[1].code, "1")
        self.assertEqual(entries[1].label, "OUI")

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_filters_out_non_nominal_unites(self, mock_get):
        """
        Les unités de type CONTINU ne génèrent aucun VocabularySet.
        """
        mock_get.side_effect = _standard_side_effect()

        sync_dsf_vocabularies_from_api()

        self.assertFalse(VocabularySet.objects.filter(code="%").exists())

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_filters_out_blacklisted_unites(self, mock_get):
        """
        Les unités présentes dans BLACKLISTED_UNITES sont ignorées même si elles sont NOMINAL.
        """
        mock_get.side_effect = _standard_side_effect()

        sync_dsf_vocabularies_from_api()

        self.assertFalse(VocabularySet.objects.filter(code="CM").exists())

    # ------------------------------------------------------------------
    # Mise à jour et désactivation
    # ------------------------------------------------------------------

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_updates_existing_entries(self, mock_get):
        """
        Les entrées existantes sont mises à jour (label, position) sans être recréées.
        """
        vocab = VocabularySet.objects.create(organisation=self.dsf_org, code="0/1", name="Ancien nom")
        VocabularyEntry.objects.create(vocabulary_set=vocab, code="0", label="Ancien label", position=99)

        mock_get.side_effect = _standard_side_effect()

        result = sync_dsf_vocabularies_from_api()

        self.assertEqual(result["entries_created"], 1)  # entrée "1" créée
        self.assertEqual(result["entries_updated"], 1)  # entrée "0" mise à jour

        entry = VocabularyEntry.objects.get(vocabulary_set=vocab, code="0")
        self.assertEqual(entry.label, "NON")
        self.assertEqual(entry.position, 0)

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_deactivates_entries_absent_from_api(self, mock_get):
        """
        Les entrées présentes en base mais absentes de l'API sont désactivées (is_active=False).
        """
        vocab = VocabularySet.objects.create(organisation=self.dsf_org, code="0/1", name="0/1")
        VocabularyEntry.objects.create(vocabulary_set=vocab, code="OBSOLETE", label="Entrée obsolète", is_active=True)

        mock_get.side_effect = _standard_side_effect()

        result = sync_dsf_vocabularies_from_api()

        self.assertEqual(result["entries_deactivated"], 1)
        obsolete = VocabularyEntry.objects.get(vocabulary_set=vocab, code="OBSOLETE")
        self.assertFalse(obsolete.is_active)

    # ------------------------------------------------------------------
    # Dry-run
    # ------------------------------------------------------------------

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_dry_run_makes_no_db_changes(self, mock_get):
        """
        En mode dry-run, aucun objet n'est créé ou modifié en base.
        """
        mock_get.side_effect = _standard_side_effect()

        sync_dsf_vocabularies_from_api(dry_run=True)

        self.assertEqual(VocabularySet.objects.count(), 0)
        self.assertEqual(VocabularyEntry.objects.count(), 0)

    # ------------------------------------------------------------------
    # Filtre par unité
    # ------------------------------------------------------------------

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_only_unite_restricts_sync_to_one_set(self, mock_get):
        """
        Avec only_unite, seule l'unité demandée est synchronisée.
        """
        # On ajoute une deuxième unité NOMINAL dans la réponse /unites
        unites_with_two = UNITES_RESPONSE + [
            {
                "unite": "ABOND",
                "proprietaire": "DSF",
                "type": "NOMINAL",
                "libelle": "Abondance",
                "definition": "TAUX DE RECOUVREMENT",
                "valmax": None,
            }
        ]
        modes_with_two = MODES_RESPONSE + [
            {
                "unite": "ABOND",
                "mode": "1",
                "position": 0,
                "classe": 0,
                "valeurint": None,
                "etendue": None,
                "hls": None,
                "rgb": None,
                "cmyk": None,
                "libelle": "FAIBLE",
                "definition": "FAIBLE",
            },
        ]
        mock_get.side_effect = [
            _make_response(json_data=unites_with_two),
            _make_response(json_data=MODES_COUNT_RESPONSE),
            _make_response(json_data=modes_with_two),
        ]

        sync_dsf_vocabularies_from_api(only_unite="0/1")

        self.assertTrue(VocabularySet.objects.filter(code="0/1").exists())
        self.assertFalse(VocabularySet.objects.filter(code="ABOND").exists())

    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_only_unite_unknown_returns_empty_result(self, mock_get):
        """
        Si only_unite ne correspond à aucune unité NOMINAL, la fonction retourne des zéros sans erreur.
        """
        mock_get.side_effect = _standard_side_effect()

        result = sync_dsf_vocabularies_from_api(only_unite="INEXISTANT")

        self.assertEqual(result["sets_created"], 0)
        self.assertEqual(VocabularySet.objects.count(), 0)

    # ------------------------------------------------------------------
    # Retry et gestion d'erreurs
    # ------------------------------------------------------------------

    @patch("organisation_specific.dsf.sync_vocabularies_api.time.sleep")
    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_retries_on_http_500_then_succeeds(self, mock_get, mock_sleep):
        """
        Une erreur HTTP 500 sur le premier appel déclenche un retry ; le second appel réussit.
        """
        mock_get.side_effect = [
            _make_response(status_code=500),  # échec /unites
            _make_response(json_data=UNITES_RESPONSE),  # retry /unites OK
            _make_response(json_data=MODES_COUNT_RESPONSE),
            _make_response(json_data=MODES_RESPONSE),
        ]

        result = sync_dsf_vocabularies_from_api()

        self.assertEqual(result["sets_created"], 1)
        # Un sleep a bien eu lieu entre les deux tentatives
        mock_sleep.assert_called_once()

    @patch("organisation_specific.dsf.sync_vocabularies_api.time.sleep")
    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_raises_dsf_api_error_after_max_retries(self, mock_get, mock_sleep):
        """
        Après MAX_RETRIES échecs consécutifs, DSFApiError est levée et aucun objet n'est créé.
        """
        mock_get.return_value = _make_response(status_code=500)

        with self.assertRaises(DSFApiError):
            sync_dsf_vocabularies_from_api()

        self.assertEqual(VocabularySet.objects.count(), 0)

    @patch("organisation_specific.dsf.sync_vocabularies_api.time.sleep")
    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_retries_on_non_json_response(self, mock_get, mock_sleep):
        """
        Une réponse HTML (non-JSON) avec status 200 déclenche un retry.
        """
        html_response = _make_response(status_code=200, content_type="text/html")
        html_response.content = b"<html>Service indisponible</html>"

        mock_get.side_effect = [
            html_response,  # /unites renvoie du HTML
            _make_response(json_data=UNITES_RESPONSE),  # retry OK
            _make_response(json_data=MODES_COUNT_RESPONSE),
            _make_response(json_data=MODES_RESPONSE),
        ]

        result = sync_dsf_vocabularies_from_api()

        self.assertEqual(result["sets_created"], 1)
        mock_sleep.assert_called_once()

    @patch("organisation_specific.dsf.sync_vocabularies_api.time.sleep")
    @patch("organisation_specific.dsf.sync_vocabularies_api.requests.get")
    def test_raises_on_network_error_after_retries(self, mock_get, mock_sleep):
        """
        Une erreur réseau persistante (ConnectionError) lève DSFApiError après MAX_RETRIES tentatives.
        """
        # requests.exceptions.ConnectionError est une sous-classe de requests.RequestException,
        # contrairement au built-in ConnectionError de Python
        mock_get.side_effect = requests.exceptions.ConnectionError("Connexion refusée")

        with self.assertRaises(DSFApiError):
            sync_dsf_vocabularies_from_api()

        # sleep appelé entre chaque tentative (MAX_RETRIES - 1 fois)
        self.assertEqual(mock_sleep.call_count, 2)
