from django.test import TestCase

from organisations.factories import OrganisationFactory
from responses.factories import ResponseFactory
from responses.models import Response, ResponseStatus
from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory

_MAP_SCHEMA = {
    "fields": [
        {"id": "localisation", "ui": {"widget": "map"}},
    ]
}
_GEO_DATA = {"localisation": {"lat": 48.8566, "lon": 2.3522}}
_GEO_DATA_2 = {"localisation": {"lat": 43.2965, "lon": 5.3698}}


class TestGeoPointPopulation(TestCase):
    def test_point_set_on_create(self):
        """
        Le point est renseigné à la création si les données contiennent des coordonnées valides
        """
        survey = SurveyFactory(json_schema=_MAP_SCHEMA)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.refresh_from_db()
        self.assertIsNotNone(response.geolocation_point)
        self.assertAlmostEqual(response.geolocation_point.x, 2.3522, places=4)
        self.assertAlmostEqual(response.geolocation_point.y, 48.8566, places=4)

    def test_point_updated_when_coords_change(self):
        """
        Le point est recalculé lorsque les données sont modifiées et que la réponse est sauvegardée
        """
        survey = SurveyFactory(json_schema=_MAP_SCHEMA)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.data = _GEO_DATA_2
        response.save()
        response.refresh_from_db()
        self.assertAlmostEqual(response.geolocation_point.x, 5.3698, places=4)
        self.assertAlmostEqual(response.geolocation_point.y, 43.2965, places=4)

    def test_point_cleared_when_coords_removed(self):
        """
        Le point est effacé si les coordonnées sont supprimées des données
        """
        survey = SurveyFactory(json_schema=_MAP_SCHEMA)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.data = {}
        response.save()
        response.refresh_from_db()
        self.assertIsNone(response.geolocation_point)

    def test_point_not_set_when_no_map_field_in_schema(self):
        """
        Aucun point n'est défini si l'enquête ne contient pas de champ de type map
        """
        survey = SurveyFactory(json_schema={"fields": [{"id": "nom", "ui": {"widget": "text"}}]})
        response = ResponseFactory(survey=survey, data={"nom": "Test", **_GEO_DATA})
        response.refresh_from_db()
        self.assertIsNone(response.geolocation_point)

    def test_point_not_set_when_schema_is_none(self):
        """
        Aucun point n'est défini si le schéma de l'enquête est null
        """
        survey = SurveyFactory(json_schema=None)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.refresh_from_db()
        self.assertIsNone(response.geolocation_point)

    def test_point_not_set_for_follow_up_response(self):
        """
        Une réponse de suivi (sans survey) ne reçoit pas de point géographique,
        même si les données contiennent des coordonnées
        """
        org = OrganisationFactory()
        parent_survey = SurveyFactory(organisation=org, json_schema=_MAP_SCHEMA)
        follow_up = SurveyFollowUpFactory(organisation=org, parent_survey=parent_survey)
        parent = ResponseFactory(survey=parent_survey, data=_GEO_DATA)
        follow_up_response = Response.objects.create(
            survey_follow_up=follow_up,
            parent_response=parent,
            data=_GEO_DATA,
            status=ResponseStatus.SUBMITTED,
        )
        self.assertIsNone(follow_up_response.geolocation_point)

    def test_point_unchanged_on_partial_update_unrelated_field(self):
        """
        Le point n'est pas recalculé lors d'une mise à jour partielle qui n'inclut
        pas les champs 'data' ou 'survey'
        """
        survey = SurveyFactory(json_schema=_MAP_SCHEMA)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.refresh_from_db()
        self.assertIsNotNone(response.geolocation_point)

        response.status = ResponseStatus.SUBMITTED
        response.save(update_fields=["status"])
        response.refresh_from_db()
        self.assertAlmostEqual(response.geolocation_point.x, 2.3522, places=4)
        self.assertAlmostEqual(response.geolocation_point.y, 48.8566, places=4)

    def test_point_recalculated_on_partial_update_of_data(self):
        """
        Le point est recalculé et sauvegardé lors d'une mise à jour partielle
        incluant explicitement le champ 'data'
        """
        survey = SurveyFactory(json_schema=_MAP_SCHEMA)
        response = ResponseFactory(survey=survey, data=_GEO_DATA)
        response.data = _GEO_DATA_2
        response.save(update_fields=["data"])
        response.refresh_from_db()
        self.assertAlmostEqual(response.geolocation_point.x, 5.3698, places=4)
        self.assertAlmostEqual(response.geolocation_point.y, 43.2965, places=4)
