from io import StringIO
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings

from organisations.factories import OrganisationFactory, PoleFactory
from surveys.factories import PlacetteSurveyFactory
from surveys.models import Placette
from users.factories import UserFactory

from organisation_specific.dsf.management.commands.import_dsf_rpp_placettes import Command

# Fausse entrée DATABASES avec dsf_ref pour débloquer la garde du début de commande
DATABASES_WITH_DSF_REF = {**settings.DATABASES, "dsf_ref": {"ENGINE": "django.db.backends.postgresql"}}

# Ligne DSF type (correspond à l'ordre de COLUMNS dans la commande)
# (code_placette, id_localisation, code_co, echelon, actif, lat, lon,
#  topo, expoliz, annee_plant, code_essence, code_essence2, long_lisiere)
SAMPLE_ROW = ("PP32191", 77754, "32O02", "T", True, 43.80928, -0.06536, "2", "6", "2024", "871", None, None)
SAMPLE_ROW_INACTIVE = ("PP05081", 35920, "04O03", "A", False, 44.12345, 1.23456, "1", "5", None, "880", "000", None)
SAMPLE_ROW_NO_COORDS = ("PP99999", 99999, None, "O", True, None, None, "3", "7", None, "871", None, None)


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
    """Retourne un mock de connections renvoyant *rows* depuis fetchall."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: mock_cursor
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = rows
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connections = MagicMock()
    mock_connections.__getitem__.return_value = mock_conn
    return mock_connections


@override_settings(DATABASES=DATABASES_WITH_DSF_REF)
@patch("organisation_specific.dsf.management.commands.import_dsf_rpp_placettes.connections")
class ImportDsfRppPlacettesTest(TestCase):
    def test_cree_placette_depuis_ligne_dsf(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        self.assertEqual(Placette.objects.count(), 1)
        p = Placette.objects.get()
        self.assertEqual(p.code, "PP32191")
        self.assertEqual(p.dsf_id_localisation, 77754)
        self.assertAlmostEqual(p.lat, 43.80928)
        self.assertAlmostEqual(p.lon, -0.06536)
        self.assertTrue(p.is_active)
        self.assertEqual(p.characteristics["topo"], "2")
        self.assertEqual(p.characteristics["code_essence"], "871")
        self.assertIsNone(p.characteristics["code_essence2"])

    def test_update_or_create_idempotent(self, mock_conns):
        """Un deuxième import met à jour la placette sans en créer une nouvelle."""
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)
        cmd.handle(dry_run=False, survey_id=None)

        self.assertEqual(Placette.objects.count(), 1)

    def test_placette_inactive_importee_comme_inactive(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW_INACTIVE])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertFalse(p.is_active)

    def test_ligne_sans_coordonnees_ignoree(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW_NO_COORDS])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        self.assertEqual(Placette.objects.count(), 0)
        self.assertIn("1 ignorée(s)", cmd.stdout.getvalue())

    def test_pole_assigne_depuis_echelon(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        org = OrganisationFactory()
        pole_t = PoleFactory(organisation=org, dsf_code="T")

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertEqual(p.pole, pole_t)

    def test_pole_null_si_echelon_inconnu(self, mock_conns):
        """Un échelon absent de la base Sylvasan laisse pole=None sans erreur."""
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        # On ne crée pas de Pole pour l'échelon "T"

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertIsNone(p.pole)

    def test_created_by_assigne_depuis_code_co(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        user = UserFactory(external_id="32O02")

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertEqual(p.created_by, user)

    def test_created_by_null_si_code_co_absent(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW_NO_COORDS])["dsf_ref"]
        # SAMPLE_ROW_NO_COORDS a code_co=None et sera ignorée (pas de coords),
        # donc on teste avec une ligne sans code_co mais avec coords
        row_sans_co = ("PP11111", 11111, None, "O", True, 47.5, 1.5, "1", "5", None, "871", None, None)
        mock_conns.__getitem__.return_value = _mock_connections([row_sans_co])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertIsNone(p.created_by)

    def test_created_by_ajoute_aux_accessors_a_la_creation(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        user = UserFactory(external_id="32O02")

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        self.assertIn(user, p.accessors.all())

    def test_created_by_non_ajoute_aux_accessors_sur_mise_a_jour(self, mock_conns):
        """Sur un re-import, les accessors existants ne sont pas modifiés."""
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        user = UserFactory(external_id="32O02")
        autre_user = UserFactory()

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        p = Placette.objects.get()
        p.accessors.add(autre_user)
        p.accessors.remove(user)  # simule une modification manuelle des accessors

        # Deuxième import : ne doit pas rétablir user dans les accessors
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        cmd2 = _make_command()
        cmd2.handle(dry_run=False, survey_id=None)

        p.refresh_from_db()
        self.assertNotIn(user, p.accessors.all())
        self.assertIn(autre_user, p.accessors.all())

    def test_rattache_au_survey_si_survey_id_fourni(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]
        survey = PlacetteSurveyFactory()

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=survey.pk)

        p = Placette.objects.get()
        self.assertEqual(p.survey, survey)

    def test_survey_id_introuvable_sort_sans_creer(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=99999)

        self.assertEqual(Placette.objects.count(), 0)
        self.assertIn("99999", cmd.stderr.getvalue())

    def test_dry_run_ne_cree_rien(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=True, survey_id=None)

        self.assertEqual(Placette.objects.count(), 0)
        self.assertIn("dry-run", cmd.stdout.getvalue())

    def test_plusieurs_lignes_toutes_importees(self, mock_conns):
        mock_conns.__getitem__.return_value = _mock_connections([SAMPLE_ROW, SAMPLE_ROW_INACTIVE])["dsf_ref"]

        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        self.assertEqual(Placette.objects.count(), 2)
        self.assertEqual(Placette.objects.filter(is_active=True).count(), 1)
        self.assertEqual(Placette.objects.filter(is_active=False).count(), 1)


class ImportDsfRppPlacettesNoDsfrRefTest(TestCase):
    @override_settings(DATABASES={k: v for k, v in settings.DATABASES.items() if k != "dsf_ref"})
    def test_sans_dsf_ref_sort_avec_erreur(self):
        """La commande s'arrête proprement si DSF_REF n'est pas configuré."""
        cmd = _make_command()
        cmd.handle(dry_run=False, survey_id=None)

        self.assertIn("indisponible", cmd.stderr.getvalue())
        self.assertEqual(Placette.objects.count(), 0)
