from django.core.exceptions import ValidationError
from django.test import TestCase

from surveys.factories import PlacetteFactory, PlacetteLevelFactory
from surveys.factories.placettenode import PlacetteNodeFactory
from surveys.factories.placettesurvey import PlacetteSurveyFactory
from surveys.models import PlacetteNode


class TestPlacetteNodeClean(TestCase):
    def setUp(self):
        self.survey = PlacetteSurveyFactory()
        self.placette = PlacetteFactory(surveys=[self.survey])

        self.root_level = PlacetteLevelFactory(placette_survey=self.survey, parent_level=None)
        self.child_level = PlacetteLevelFactory(placette_survey=self.survey, parent_level=self.root_level)
        self.grandchild_level = PlacetteLevelFactory(placette_survey=self.survey, parent_level=self.child_level)

        self.other_survey = PlacetteSurveyFactory()
        self.other_root_level = PlacetteLevelFactory(placette_survey=self.other_survey, parent_level=None)

    # --- Cas valides ---

    def test_noeud_racine_sans_parent_valide(self):
        """Un nœud de niveau racine sans parent est valide."""
        node = PlacetteNode(placette=self.placette, level=self.root_level, parent=None)
        node.clean()  # ne doit pas lever d'exception

    def test_noeud_enfant_avec_parent_correct_valide(self):
        """Un nœud dont le parent est au niveau parent attendu est valide."""
        parent_node = PlacetteNodeFactory(placette=self.placette, level=self.root_level, parent=None)
        node = PlacetteNode(placette=self.placette, level=self.child_level, parent=parent_node)
        node.clean()

    def test_noeud_petit_enfant_avec_parent_correct_valide(self):
        """La validation fonctionne sur plusieurs niveaux d'imbrication."""
        root_node = PlacetteNodeFactory(placette=self.placette, level=self.root_level, parent=None)
        child_node = PlacetteNodeFactory(placette=self.placette, level=self.child_level, parent=root_node)
        node = PlacetteNode(placette=self.placette, level=self.grandchild_level, parent=child_node)
        node.clean()

    # --- Cas invalides ---

    def test_noeud_racine_avec_parent_leve_erreur(self):
        """Un nœud de niveau racine ne peut pas avoir de nœud parent."""
        parent_node = PlacetteNodeFactory(placette=self.placette, level=self.root_level, parent=None)
        node = PlacetteNode(placette=self.placette, level=self.root_level, parent=parent_node)
        with self.assertRaises(ValidationError):
            node.clean()

    def test_noeud_non_racine_sans_parent_leve_erreur(self):
        """Un nœud de niveau non-racine sans parent est invalide."""
        node = PlacetteNode(placette=self.placette, level=self.child_level, parent=None)
        with self.assertRaises(ValidationError):
            node.clean()

    def test_noeud_avec_parent_mauvais_niveau_leve_erreur(self):
        """Un nœud dont le parent n'est pas au niveau parent attendu est invalide."""
        wrong_parent = PlacetteNodeFactory(placette=self.placette, level=self.root_level, parent=None)
        # grandchild attend un parent au niveau child, pas root
        node = PlacetteNode(placette=self.placette, level=self.grandchild_level, parent=wrong_parent)
        with self.assertRaises(ValidationError):
            node.clean()

    def test_noeud_avec_parent_niveau_autre_protocole_leve_erreur(self):
        """Un nœud dont le parent appartient à un niveau d'un autre protocole est invalide."""
        other_parent = PlacetteNodeFactory(placette=self.placette, level=self.other_root_level, parent=None)
        node = PlacetteNode(placette=self.placette, level=self.child_level, parent=other_parent)
        with self.assertRaises(ValidationError):
            node.clean()

    def test_noeud_sautant_un_niveau_leve_erreur(self):
        """Un nœud de niveau petit-enfant parented directement à un nœud racine est invalide."""
        root_node = PlacetteNodeFactory(placette=self.placette, level=self.root_level, parent=None)
        node = PlacetteNode(placette=self.placette, level=self.grandchild_level, parent=root_node)
        with self.assertRaises(ValidationError):
            node.clean()
