import datetime

from django.contrib.gis.geos import Point
from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory

from responses.factories import ResponseFactory
from responses.views.response_geo import GEO_RESPONSE_LIMIT

# Boîte englobante centrée sur Paris, utilisée dans tous les tests
BBOX_PARIS = {"south": 48.7, "west": 2.2, "north": 49.0, "east": 2.5}

# Un point à l'intérieur de BBOX_PARIS
POINT_PARIS = Point(2.35, 48.85, srid=4326)

# Un point en dehors de BBOX_PARIS (Lyon)
POINT_LYON = Point(4.83, 45.74, srid=4326)

GEO_URL = reverse("response_geo_list")


def _geo_response(survey, point=POINT_PARIS):
    """Crée une réponse avec un point géographique pré-renseigné."""
    r = ResponseFactory(survey=survey)
    r.geolocation_point = point
    r.save(update_fields=["geolocation_point"])
    return r


class TestResponseGeoAuthentification(APITestCase):
    def test_non_authentifie_recoit_401(self):
        """
        Un·e utilisateur·ice non authentifié·e ne peut pas accéder à l'endpoint géo
        """
        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestResponseGeoParamsBbox(APITestCase):
    @authenticate
    def test_params_manquants_retournent_400(self):
        """
        Une requête sans les quatre paramètres de bounding box retourne une 400
        """
        response = self.client.get(GEO_URL, {"south": 48.7, "west": 2.2})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_params_non_numeriques_retournent_400(self):
        """
        Des paramètres de bounding box non numériques retournent une 400
        """
        response = self.client.get(GEO_URL, {"south": "abc", "west": 2.2, "north": 49.0, "east": 2.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_bbox_incoherente_retourne_400(self):
        """
        Une bounding box où south >= north est invalide et retourne une 400
        """
        response = self.client.get(GEO_URL, {"south": 49.0, "west": 2.2, "north": 48.7, "east": 2.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestResponseGeoAccesParMembership(APITestCase):
    @authenticate
    def test_sans_membership_retourne_liste_vide(self):
        """
        Un·e utilisateur·ice authentifié·e sans aucun rôle obtient une liste vide
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @authenticate
    def test_admin_org_voit_reponses_dans_la_zone(self):
        """
        Un·e admin d'organisation voit toutes les réponses de cette organisation dans la zone
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)
        _geo_response(survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @authenticate
    def test_responder_voit_reponses_de_ses_collegues_dans_la_zone(self):
        """
        Un·e responder voit aussi les réponses de ses collègues dans la zone —
        ce comportement est différent de l'endpoint /api/mobile/responses/ qui
        ne retourne que ses propres réponses
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)  # réponse d'un autre utilisateur
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @authenticate
    def test_admin_pole_voit_reponses_de_son_pole(self):
        """
        Un·e admin de pôle voit les réponses des enquêtes de son pôle dans la zone
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey = SurveyFactory(organisation=org, pole=pole)
        _geo_response(survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @authenticate
    def test_admin_pole_voit_reponses_enquetes_org(self):
        """
        Un·e admin de pôle voit aussi les réponses des enquêtes au niveau organisation
        (sans pôle) dans la zone
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        survey_org = SurveyFactory(organisation=org, pole=None)
        _geo_response(survey_org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @authenticate
    def test_admin_pole_ne_voit_pas_reponses_autre_pole(self):
        """
        Un·e admin de pôle ne voit pas les réponses des enquêtes d'un autre pôle
        """
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        survey_autre_pole = SurveyFactory(organisation=org, pole=autre_pole)
        _geo_response(survey_autre_pole)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @authenticate
    def test_reponse_autre_organisation_invisible(self):
        """
        Une réponse appartenant à une autre organisation n'est pas visible,
        même si elle est dans la zone
        """
        autre_org = OrganisationFactory()
        survey_autre = SurveyFactory(organisation=autre_org)
        _geo_response(survey_autre)

        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class TestResponseGeoFiltrageSpatial(APITestCase):
    @authenticate
    def test_reponse_hors_zone_non_retournee(self):
        """
        Une réponse dont le point est hors de la bounding box n'est pas retournée
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey, point=POINT_LYON)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @authenticate
    def test_seules_les_reponses_dans_la_zone_sont_retournees(self):
        """
        Parmi plusieurs réponses, seules celles dans la bounding box sont retournées
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        dans_zone = _geo_response(survey, point=POINT_PARIS)
        _geo_response(survey, point=POINT_LYON)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], dans_zone.id)

    @authenticate
    def test_reponse_sans_point_geo_exclue(self):
        """
        Une réponse sans point géographique n'est pas retournée,
        même si elle appartient à l'organisation
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        ResponseFactory(survey=survey, geolocation_point=None)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class TestResponseGeoPayload(APITestCase):
    @authenticate
    def test_payload_contient_les_champs_attendus(self):
        """
        Chaque élément du payload contient les champs nécessaires pour l'affichage sur la carte :
        id, survey_id, survey_title, status, creation_date, lat, lon
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org, title="Enquête arbres")
        _geo_response(survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        item = response.data[0]
        self.assertIn("id", item)
        self.assertIn("survey_id", item)
        self.assertIn("survey_title", item)
        self.assertIn("status", item)
        self.assertIn("creation_date", item)
        self.assertIn("lat", item)
        self.assertIn("lon", item)
        self.assertEqual(item["survey_title"], "Enquête arbres")
        self.assertAlmostEqual(item["lat"], POINT_PARIS.y, places=4)
        self.assertAlmostEqual(item["lon"], POINT_PARIS.x, places=4)


class TestResponseGeoLimite(APITestCase):
    @authenticate
    def test_nombre_de_reponses_limite_a_200(self):
        """
        L'endpoint ne retourne pas plus de GEO_RESPONSE_LIMIT réponses,
        même si davantage correspondent aux critères
        """
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        from responses.models import Response, ResponseStatus

        Response.objects.bulk_create(
            [
                Response(survey=survey, data={}, status=ResponseStatus.SUBMITTED, geolocation_point=POINT_PARIS)
                for _ in range(GEO_RESPONSE_LIMIT + 1)
            ]
        )

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), GEO_RESPONSE_LIMIT)


class TestResponseGeoFiltres(APITestCase):
    """Tests des paramètres de filtrage optionnels : surveys, after, before, only_mine."""

    def setUp(self):
        self.org = OrganisationFactory()
        self.survey_a = SurveyFactory(organisation=self.org)
        self.survey_b = SurveyFactory(organisation=self.org)

    def _membre(self):
        MembershipFactory(user=authenticate.user, organisation=self.org, membership_type=MembershipType.ADMIN)

    # --- surveys ---

    @authenticate
    def test_filtre_surveys_retourne_seulement_enquete_demandee(self):
        """
        Le paramètre surveys=<id> restreint les résultats à cette enquête
        """
        self._membre()
        reponse_a = _geo_response(self.survey_a)
        _geo_response(self.survey_b)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": str(self.survey_a.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], reponse_a.id)

    @authenticate
    def test_filtre_surveys_accepte_plusieurs_ids(self):
        """
        surveys=id1,id2 retourne les réponses des deux enquêtes
        """
        self._membre()
        survey_c = SurveyFactory(organisation=self.org)
        _geo_response(self.survey_a)
        _geo_response(self.survey_b)
        _geo_response(survey_c)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": f"{self.survey_a.id},{self.survey_b.id}"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @authenticate
    def test_filtre_surveys_non_numerique_retourne_400(self):
        """
        surveys=abc retourne une erreur 400
        """
        self._membre()
        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- after ---

    @authenticate
    def test_filtre_after_exclut_reponses_anterieures(self):
        """
        after=YYYY-MM-DD ne retourne que les réponses créées ce jour ou après
        """
        self._membre()
        ancienne = _geo_response(self.survey_a)
        ancienne.creation_date = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)
        ancienne.save(update_fields=["creation_date"])

        recente = _geo_response(self.survey_a)
        recente.creation_date = datetime.datetime(2025, 6, 1, tzinfo=datetime.UTC)
        recente.save(update_fields=["creation_date"])

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "after": "2025-01-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data]
        self.assertIn(recente.id, ids)
        self.assertNotIn(ancienne.id, ids)

    @authenticate
    def test_filtre_after_format_invalide_retourne_400(self):
        """
        after=31/12/2024 (format non ISO) retourne une erreur 400
        """
        self._membre()
        response = self.client.get(GEO_URL, {**BBOX_PARIS, "after": "31/12/2024"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- before ---

    @authenticate
    def test_filtre_before_exclut_reponses_posterieures(self):
        """
        before=YYYY-MM-DD ne retourne que les réponses créées ce jour ou avant
        """
        self._membre()
        ancienne = _geo_response(self.survey_a)
        ancienne.creation_date = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)
        ancienne.save(update_fields=["creation_date"])

        recente = _geo_response(self.survey_a)
        recente.creation_date = datetime.datetime(2025, 6, 1, tzinfo=datetime.UTC)
        recente.save(update_fields=["creation_date"])

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "before": "2024-12-31"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data]
        self.assertIn(ancienne.id, ids)
        self.assertNotIn(recente.id, ids)

    @authenticate
    def test_filtre_before_format_invalide_retourne_400(self):
        """
        before=not-a-date retourne une erreur 400
        """
        self._membre()
        response = self.client.get(GEO_URL, {**BBOX_PARIS, "before": "not-a-date"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- only_mine ---

    @authenticate
    def test_filtre_only_mine_exclut_reponses_des_collegues(self):
        """
        only_mine=true ne retourne que les réponses dont l'auteur est l'utilisateur connecté
        """
        self._membre()
        ma_reponse = _geo_response(self.survey_a)
        ma_reponse.respondant = authenticate.user
        ma_reponse.save(update_fields=["respondant"])

        _geo_response(self.survey_a)  # réponse d'un autre utilisateur

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "only_mine": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], ma_reponse.id)

    @authenticate
    def test_filtre_only_mine_false_retourne_toutes_les_reponses(self):
        """
        only_mine=false (ou absent) retourne toutes les réponses accessibles
        """
        self._membre()
        _geo_response(self.survey_a)
        _geo_response(self.survey_a)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "only_mine": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # --- combinaison de filtres ---

    @authenticate
    def test_filtres_surveys_et_only_mine_combines(self):
        """
        surveys + only_mine=true ne retourne que les réponses de l'enquête ciblée
        dont l'auteur est l'utilisateur connecté
        """
        self._membre()
        ma_reponse = _geo_response(self.survey_a)
        ma_reponse.respondant = authenticate.user
        ma_reponse.save(update_fields=["respondant"])

        _geo_response(self.survey_a)  # collègue, même enquête
        _geo_response(self.survey_b)  # moi, autre enquête — exclu par surveys

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": str(self.survey_a.id), "only_mine": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], ma_reponse.id)
