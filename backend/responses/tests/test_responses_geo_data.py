from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory
from surveys.factories.surveyfollowup import SurveyFollowUpFactory
from users.factories import UserFactory

from responses.factories import ResponseFactory
from responses.models import Response, ResponseStatus

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


_GEO_URL = reverse("response_geo_list")
_BBOX_PARIS = {"south": 48.7, "west": 2.2, "north": 49.0, "east": 2.5}
_POINT_PARIS = Point(2.35, 48.85, srid=4326)


def _geo_response(survey):
    r = ResponseFactory(survey=survey)
    r.geolocation_point = _POINT_PARIS
    r.save(update_fields=["geolocation_point"])
    return r


def _follow_up_response(parent, survey_follow_up, respondant=None):
    return Response.objects.create(
        survey_follow_up=survey_follow_up,
        parent_response=parent,
        data={},
        status=ResponseStatus.SUBMITTED,
        respondant=respondant,
    )


class TestResponseGeoFollowUps(APITestCase):
    @authenticate
    def test_no_follow_ups_returns_empty_list(self):
        """
        Une réponse sans aucune réponse de suivi expose un tableau follow_ups vide
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(_GEO_URL, _BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["follow_ups"], [])

    @authenticate
    def test_follow_up_fields_are_serialized(self):
        """
        Une réponse de suivi est sérialisée avec son id, sa date, les infos de l'étape
        (titre, couleur, icône) et le répondant
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(
            parent_survey=survey,
            organisation=org,
            title="Signaler une anomalie",
            action_color="#fde39c",
            action_icon="ri-eye-line",
        )
        parent = _geo_response(survey)
        respondant = UserFactory()
        fu_response = _follow_up_response(parent, follow_up, respondant=respondant)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(_GEO_URL, _BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow_ups = response.json()[0]["followUps"]
        self.assertEqual(len(follow_ups), 1)

        item = follow_ups[0]
        self.assertEqual(item["id"], fu_response.id)
        self.assertIn("creationDate", item)
        self.assertEqual(item["survey"]["title"], "Signaler une anomalie")
        self.assertEqual(item["survey"]["actionColor"], "#fde39c")
        self.assertEqual(item["survey"]["actionIcon"], "ri-eye-line")
        self.assertEqual(item["respondant"]["id"], respondant.id)
        self.assertEqual(item["respondant"]["firstName"], respondant.first_name)
        self.assertEqual(item["respondant"]["lastName"], respondant.last_name)

    @authenticate
    def test_follow_ups_ordered_most_recent_first(self):
        """
        Plusieurs réponses de suivi sont retournées du plus récent au plus ancien
        """
        from datetime import timedelta
        from django.utils import timezone

        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(parent_survey=survey, organisation=org)
        parent = _geo_response(survey)
        fu1 = _follow_up_response(parent, follow_up)
        fu2 = _follow_up_response(parent, follow_up)
        fu3 = _follow_up_response(parent, follow_up)
        now = timezone.now()
        # Forcer des dates distinctes pour s'affranchir de la résolution temporelle du test
        Response.objects.filter(id=fu1.id).update(creation_date=now - timedelta(hours=2))
        Response.objects.filter(id=fu2.id).update(creation_date=now - timedelta(hours=1))
        Response.objects.filter(id=fu3.id).update(creation_date=now)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(_GEO_URL, _BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data[0]["follow_ups"]]
        self.assertEqual(ids, [fu3.id, fu2.id, fu1.id])

    @authenticate
    def test_follow_up_visible_regardless_of_creator(self):
        """
        L'accès à une réponse parente donne accès à toutes ses réponses de suivi,
        même si celles-ci ont été créées par un utilisateur d'une autre organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(parent_survey=survey, organisation=org)
        parent = _geo_response(survey)
        external_user = UserFactory()
        fu_response = _follow_up_response(parent, follow_up, respondant=external_user)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(_GEO_URL, _BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow_ups = response.data[0]["follow_ups"]
        self.assertEqual(len(follow_ups), 1)
        self.assertEqual(follow_ups[0]["id"], fu_response.id)
        self.assertEqual(follow_ups[0]["respondant"]["id"], external_user.id)

    @authenticate
    def test_inactive_follow_up_excluded(self):
        """
        Une réponse de suivi désactivée (is_active=False) n'apparaît pas dans follow_ups
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        follow_up = SurveyFollowUpFactory(parent_survey=survey, organisation=org)
        parent = _geo_response(survey)
        fu_response = _follow_up_response(parent, follow_up)
        fu_response.is_active = False
        fu_response.save(update_fields=["is_active"])
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(_GEO_URL, _BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["follow_ups"], [])
