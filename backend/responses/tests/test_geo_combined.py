from django.contrib.gis.geos import Point
from django.urls import reverse

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory, PoleFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import PlacetteFactory, PlacetteSurveyFactory, SurveyFactory

from responses.factories import ResponseFactory

BBOX_PARIS = {"south": 48.7, "west": 2.2, "north": 49.0, "east": 2.5}
POINT_PARIS = Point(2.35, 48.85, srid=4326)
POINT_LYON = Point(4.83, 45.74, srid=4326)

GEO_URL = reverse("combined_geo")


def _geo_response(survey, point=POINT_PARIS):
    r = ResponseFactory(survey=survey)
    r.geolocation_point = point
    r.save(update_fields=["geolocation_point"])
    return r


def _placette(survey, lat=48.85, lon=2.35):
    return PlacetteFactory(surveys=[survey], lat=lat, lon=lon)


class TestCombinedGeoAuthentification(APITestCase):
    def test_non_authentifie_recoit_401(self):
        """Un·e utilisateur·ice non authentifié·e ne peut pas accéder à l'endpoint."""
        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestCombinedGeoParamsBbox(APITestCase):
    @authenticate
    def test_params_manquants_retournent_400(self):
        """Une requête sans les quatre paramètres de bounding box retourne une 400."""
        response = self.client.get(GEO_URL, {"south": 48.7, "west": 2.2})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_bbox_incoherente_retourne_400(self):
        """Une bounding box où south >= north retourne une 400."""
        response = self.client.get(GEO_URL, {"south": 49.0, "west": 2.2, "north": 48.7, "east": 2.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestCombinedGeoShape(APITestCase):
    @authenticate
    def test_reponse_contient_responses_et_placettes(self):
        """Le payload contient les clés 'responses' et 'placettes'."""
        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("responses", response.data)
        self.assertIn("placettes", response.data)

    @authenticate
    def test_sans_membership_retourne_listes_vides(self):
        """Un·e utilisateur·ice sans rôle obtient deux listes vides."""
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)
        placette_survey = PlacetteSurveyFactory(organisation=org)
        _placette(placette_survey)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["responses"], [])
        self.assertEqual(response.data["placettes"], [])


class TestCombinedGeoResponses(APITestCase):
    @authenticate
    def test_membre_voit_reponses_dans_la_zone(self):
        """Un·e membre d'organisation voit les réponses géolocalisées dans la zone."""
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["responses"]), 1)

    @authenticate
    def test_reponse_hors_zone_exclue(self):
        """Une réponse hors bbox n'est pas retournée."""
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey, point=POINT_LYON)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["responses"], [])

    @authenticate
    def test_filtre_surveys(self):
        """Le paramètre surveys= restreint les réponses aux enquêtes demandées."""
        org = OrganisationFactory()
        survey_a = SurveyFactory(organisation=org)
        survey_b = SurveyFactory(organisation=org)
        reponse_a = _geo_response(survey_a)
        _geo_response(survey_b)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": str(survey_a.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["responses"]), 1)
        self.assertEqual(response.data["responses"][0]["id"], reponse_a.id)

    @authenticate
    def test_filtre_surveys_non_numerique_retourne_400(self):
        """surveys=abc retourne une 400."""
        MembershipFactory(user=authenticate.user, organisation=OrganisationFactory())
        response = self.client.get(GEO_URL, {**BBOX_PARIS, "surveys": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestCombinedGeoPlacettes(APITestCase):
    @authenticate
    def test_membre_voit_placettes_dans_la_zone(self):
        """Un·e membre voit les placettes publiées de son organisation dans la zone."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True)
        p = _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["placettes"]), 1)
        self.assertEqual(response.data["placettes"][0]["id"], p.id)

    @authenticate
    def test_placette_hors_zone_exclue(self):
        """Une placette hors bbox n'est pas retournée."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True)
        _placette(placette_survey, lat=45.74, lon=4.83)  # Lyon
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_protocole_non_publie_exclu(self):
        """Les placettes d'un protocole non publié ne sont pas retournées."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=False)
        _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_protocole_inactif_exclu(self):
        """Les placettes d'un protocole soft-deleté ne sont pas retournées."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True, is_active=False)
        _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_placette_inactive_exclue(self):
        """Une placette soft-deletée n'est pas retournée."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True)
        _placette(placette_survey)
        PlacetteFactory(surveys=[placette_survey], lat=48.85, lon=2.35, is_active=False)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["placettes"]), 1)

    @authenticate
    def test_placette_autre_organisation_invisible(self):
        """Une placette d'une autre organisation n'est pas visible."""
        autre_org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=autre_org, is_published=True)
        _placette(placette_survey)

        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_membre_pole_voit_placettes_de_son_pole(self):
        """Un·e membre de pôle voit les placettes de ce pôle."""
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        placette_survey = PlacetteSurveyFactory(organisation=org, pole=pole, is_published=True)
        p = _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["placettes"]), 1)
        self.assertEqual(response.data["placettes"][0]["id"], p.id)

    @authenticate
    def test_membre_pole_voit_placettes_sans_pole_de_lorg(self):
        """Un·e membre de pôle voit aussi les placettes de l'organisation sans pôle."""
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        placette_survey_org = PlacetteSurveyFactory(organisation=org, pole=None, is_published=True)
        p = _placette(placette_survey_org)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["placettes"]), 1)
        self.assertEqual(response.data["placettes"][0]["id"], p.id)

    @authenticate
    def test_membre_pole_ne_voit_pas_placettes_autre_pole(self):
        """Un·e membre de pôle ne voit pas les placettes d'un autre pôle."""
        org = OrganisationFactory()
        pole = PoleFactory(organisation=org)
        autre_pole = PoleFactory(organisation=org)
        placette_survey = PlacetteSurveyFactory(organisation=org, pole=autre_pole, is_published=True)
        _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, pole=pole, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_filtre_placette_surveys(self):
        """Le paramètre placette_surveys= restreint les placettes au(x) protocole(s) demandé(s)."""
        org = OrganisationFactory()
        survey_a = PlacetteSurveyFactory(organisation=org, is_published=True)
        survey_b = PlacetteSurveyFactory(organisation=org, is_published=True)
        p_a = _placette(survey_a)
        _placette(survey_b)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "placette_surveys": str(survey_a.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["placettes"]), 1)
        self.assertEqual(response.data["placettes"][0]["id"], p_a.id)

    @authenticate
    def test_filtre_placette_surveys_protocole_autre_org_invisible(self):
        """Un protocole d'une autre organisation ne peut pas être utilisé pour découvrir
        des placettes via le filtre placette_surveys=, même si la placette appartient aussi
        à un protocole accessible (fuite via JOIN M2M indépendant)."""
        org = OrganisationFactory()
        autre_org = OrganisationFactory()
        survey_own = PlacetteSurveyFactory(organisation=org, is_published=True)
        survey_other = PlacetteSurveyFactory(organisation=autre_org, is_published=True)
        # La placette appartient aux deux protocoles
        PlacetteFactory(surveys=[survey_own, survey_other], lat=48.85, lon=2.35)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, {**BBOX_PARIS, "placette_surveys": str(survey_other.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["placettes"], [])

    @authenticate
    def test_filtre_placette_surveys_non_numerique_retourne_400(self):
        """placette_surveys=abc retourne une 400."""
        MembershipFactory(user=authenticate.user, organisation=OrganisationFactory())
        response = self.client.get(GEO_URL, {**BBOX_PARIS, "placette_surveys": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_payload_placette_contient_champs_attendus(self):
        """Chaque placette du payload contient id, lat, lon, label, placette_surveys, characteristics."""
        org = OrganisationFactory()
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True, name="Protocole test")
        _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["placettes"][0]
        for field in ("id", "lat", "lon", "label", "placette_surveys", "characteristics"):
            self.assertIn(field, item)
        self.assertEqual(item["placette_surveys"][0]["name"], "Protocole test")


class TestCombinedGeoMixte(APITestCase):
    @authenticate
    def test_responses_et_placettes_retournees_ensemble(self):
        """Réponses et placettes sont bien retournées dans le même appel."""
        org = OrganisationFactory()
        survey = SurveyFactory(organisation=org)
        _geo_response(survey)
        placette_survey = PlacetteSurveyFactory(organisation=org, is_published=True)
        _placette(placette_survey)
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(GEO_URL, BBOX_PARIS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["responses"]), 1)
        self.assertEqual(len(response.data["placettes"]), 1)
