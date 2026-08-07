import csv
import io
import json

from django.urls import reverse
from django.utils import timezone

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory

from responses.factories import ResponseFactory
from users.factories import UserFactory


class TestJsonExport(APITestCase):
    def test_unauthenticated_cannot_export(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        response = self.client.get(reverse("response_export_json"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_json_attachment(self):
        """
        La réponse est un fichier JSON en pièce jointe
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        ResponseFactory(survey=SurveyFactory(organisation=org))

        response = self.client.get(reverse("response_export_json"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/json", response["Content-Type"])
        self.assertIn('attachment; filename="reponses.json"', response["Content-Disposition"])

    @authenticate
    def test_export_contains_all_accessible_responses(self):
        """
        L'export contient toutes les réponses accessibles, sans pagination
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        response_a = ResponseFactory(survey=survey)
        response_b = ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_export_json"))

        data = json.loads(response.content)
        ids = [item["id"] for item in data]
        self.assertIn(response_a.id, ids)
        self.assertIn(response_b.id, ids)

    @authenticate
    def test_json_survey_is_object_with_id_and_title(self):
        """
        L'export JSON représente l'enquête comme un objet avec id et title
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org, title="Enquête de satisfaction")
        ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_export_json"))

        data = json.loads(response.content)
        survey_data = data[0]["survey"]
        self.assertEqual(survey_data["id"], survey.id)
        self.assertEqual(survey_data["title"], "Enquête de satisfaction")

    @authenticate
    def test_json_respondant_includes_email_and_external_id(self):
        """
        L'export JSON inclut l'email et l'identifiant externe du répondant
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        respondant = UserFactory(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            external_id="EXT-42",
        )
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=respondant)

        response = self.client.get(reverse("response_export_json"))

        data = json.loads(response.content)
        respondant_data = data[0]["respondant"]
        self.assertEqual(respondant_data["email"], "alice@example.com")
        self.assertEqual(respondant_data["external_id"], "EXT-42")
        self.assertEqual(respondant_data["first_name"], "Alice")
        self.assertEqual(respondant_data["last_name"], "Martin")

    @authenticate
    def test_json_respondant_external_id_null_when_not_set(self):
        """
        L'identifiant externe est null dans l'export JSON quand le répondant n'en a pas
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        respondant = UserFactory(external_id=None)
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=respondant)

        response = self.client.get(reverse("response_export_json"))

        data = json.loads(response.content)
        self.assertIsNone(data[0]["respondant"]["external_id"])

    @authenticate
    def test_export_excludes_inaccessible_responses(self):
        """
        L'export ne contient pas les réponses auxquelles l'utilisateur·ice n'a pas accès
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        ResponseFactory(survey=SurveyFactory(organisation=other_org))

        response = self.client.get(reverse("response_export_json"))

        data = json.loads(response.content)
        self.assertEqual(data, [])

    @authenticate
    def test_export_filters_by_created_after(self):
        """
        Le filtre created_after exclut les réponses créées avant la date donnée
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        old_response = ResponseFactory(survey=survey)
        recent_response = ResponseFactory(survey=survey)

        # On force la date de création de la réponse ancienne dans le passé
        from responses.models import Response as ResponseModel

        ResponseModel.objects.filter(pk=old_response.pk).update(creation_date=timezone.now().replace(year=2000))

        response = self.client.get(
            reverse("response_export_json"),
            {"created_after": "2020-01-01"},
        )

        data = json.loads(response.content)
        ids = [item["id"] for item in data]
        self.assertIn(recent_response.id, ids)
        self.assertNotIn(old_response.id, ids)

    @authenticate
    def test_export_filters_by_created_before(self):
        """
        Le filtre created_before exclut les réponses créées après la date donnée
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        old_response = ResponseFactory(survey=survey)
        recent_response = ResponseFactory(survey=survey)

        from responses.models import Response as ResponseModel

        ResponseModel.objects.filter(pk=recent_response.pk).update(creation_date=timezone.now().replace(year=2099))

        response = self.client.get(
            reverse("response_export_json"),
            {"created_before": "2030-01-01"},
        )

        data = json.loads(response.content)
        ids = [item["id"] for item in data]
        self.assertIn(old_response.id, ids)
        self.assertNotIn(recent_response.id, ids)


class TestCsvExport(APITestCase):
    def test_unauthenticated_cannot_export(self):
        """
        Un·e utilisateur·ice non authentifié·e reçoit une 401
        """
        response = self.client.get(reverse("response_export_csv"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_returns_csv_attachment(self):
        """
        La réponse est un fichier CSV en pièce jointe
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        ResponseFactory(survey=SurveyFactory(organisation=org))

        response = self.client.get(reverse("response_export_csv"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn('attachment; filename="reponses.csv"', response["Content-Disposition"])

    @authenticate
    def test_csv_has_bom_for_excel_compatibility(self):
        """
        Le fichier CSV commence par un BOM UTF-8 pour être lisible sous Excel
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(reverse("response_export_csv"))

        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))

    @authenticate
    def test_csv_contains_header_row(self):
        """
        Le fichier CSV contient une ligne d'en-tête avec les noms de colonnes attendus
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        header = next(reader)
        self.assertEqual(
            header,
            [
                "ID",
                "ID enquête",
                "Titre de l'enquête",
                "ID externe répondant",
                "Email répondant",
                "Répondant",
                "Statut",
                "Date de création",
                "Données",
            ],
        )

    @authenticate
    def test_csv_survey_columns_contain_id_and_title(self):
        """
        Les colonnes enquête du CSV contiennent l'ID et le titre de l'enquête
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org, title="Enquête de satisfaction")
        ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        next(reader)  # on ignore l'en-tête
        row = next(reader)
        self.assertEqual(row[1], str(survey.id))
        self.assertEqual(row[2], "Enquête de satisfaction")

    @authenticate
    def test_csv_respondant_columns_contain_correct_data(self):
        """
        Les colonnes répondant du CSV contiennent l'ID externe, l'email et le nom complet
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        respondant = UserFactory(
            first_name="Alice",
            last_name="Martin",
            email="alice@example.com",
            external_id="EXT-42",
        )
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=respondant)

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        next(reader)  # on ignore l'en-tête
        row = next(reader)
        self.assertEqual(row[3], "EXT-42")
        self.assertEqual(row[4], "alice@example.com")
        self.assertEqual(row[5], "Alice Martin")

    @authenticate
    def test_csv_respondant_external_id_empty_when_not_set(self):
        """
        La colonne ID externe est vide quand le répondant n'en a pas
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        respondant = UserFactory(external_id=None)
        ResponseFactory(survey=SurveyFactory(organisation=org), respondant=respondant)

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        next(reader)  # on ignore l'en-tête
        row = next(reader)
        self.assertEqual(row[3], "")

    @authenticate
    def test_csv_contains_one_row_per_response(self):
        """
        Le fichier CSV contient une ligne de données par réponse accessible
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        ResponseFactory(survey=survey)
        ResponseFactory(survey=survey)

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        rows = list(reader)
        self.assertEqual(len(rows), 3)  # 1 en-tête + 2 réponses

    @authenticate
    def test_csv_excludes_inaccessible_responses(self):
        """
        L'export CSV ne contient pas les réponses auxquelles l'utilisateur·ice n'a pas accès
        """
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        ResponseFactory(survey=SurveyFactory(organisation=other_org))

        response = self.client.get(reverse("response_export_csv"))

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        rows = list(reader)
        self.assertEqual(len(rows), 1)  # en-tête uniquement

    @authenticate
    def test_csv_filters_by_date(self):
        """
        Les filtres de date fonctionnent sur l'export CSV comme sur l'export JSON
        """
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        old_response = ResponseFactory(survey=survey)
        recent_response = ResponseFactory(survey=survey)

        from responses.models import Response as ResponseModel

        ResponseModel.objects.filter(pk=old_response.pk).update(creation_date=timezone.now().replace(year=2000))

        response = self.client.get(
            reverse("response_export_csv"),
            {"created_after": "2020-01-01"},
        )

        reader = csv.reader(io.StringIO(response.content.decode("utf-8-sig")))
        rows = list(reader)
        data_rows = rows[1:]  # on ignore l'en-tête
        ids = [int(row[0]) for row in data_rows]
        self.assertIn(recent_response.id, ids)
        self.assertNotIn(old_response.id, ids)
