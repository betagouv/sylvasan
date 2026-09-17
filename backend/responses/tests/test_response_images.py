import datetime

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from common.utils import authenticate
from organisations.factories import MembershipFactory, OrganisationFactory
from organisations.models import MembershipType
from rest_framework import status
from rest_framework.test import APITestCase
from surveys.factories import SurveyFactory

from responses.factories import ResponseFactory
from responses.models import ResponseImage


def _make_image(response):
    """Crée un ResponseImage minimal lié à une réponse."""
    return ResponseImage.objects.create(
        response=response,
        file=ContentFile(b"img", name="test.jpg"),
        thumbnail=ContentFile(b"thumb", name="test_thumb.jpg"),
    )


def _response_images_url(org_id):
    return reverse("response_images_list", kwargs={"org_id": org_id})


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class TestResponseImagesListView(APITestCase):
    def test_unauthenticated_returns_401(self):
        org = OrganisationFactory()
        response = self.client.get(_response_images_url(org.id), {"start": "2024-01-01", "end": "2024-02-01"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_responder_returns_403(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.RESPONDER)
        response = self.client.get(_response_images_url(org.id), {"start": "2024-01-01", "end": "2024-02-01"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_admin_of_other_org_returns_403(self):
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=other_org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"start": "2024-01-01", "end": "2024-02-01"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_missing_start_returns_400(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"end": "2024-02-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_missing_end_returns_400(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"start": "2024-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_invalid_date_format_returns_400(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"start": "01/01/2024", "end": "2024-02-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_start_after_end_returns_400(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"start": "2024-06-01", "end": "2024-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_start_equal_end_returns_400(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        response = self.client.get(_response_images_url(org.id), {"start": "2024-01-01", "end": "2024-01-01"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @authenticate
    def test_admin_gets_org_images(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        img = _make_image(resp)

        response = self.client.get(_response_images_url(org.id), {"start": "2020-01-01", "end": "2030-01-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 1)
        result = data["results"][0]
        self.assertEqual(result["id"], img.id)
        self.assertEqual(result["responseId"], resp.id)
        self.assertIn("fileUrl", result)

    @authenticate
    def test_only_returns_images_of_requested_org(self):
        org = OrganisationFactory()
        other_org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)
        other_survey = SurveyFactory(organisation=other_org)

        own_resp = ResponseFactory(survey=survey)
        _make_image(own_resp)
        other_resp = ResponseFactory(survey=other_survey)
        _make_image(other_resp)

        response = self.client.get(_response_images_url(org.id), {"start": "2020-01-01", "end": "2030-01-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    @authenticate
    def test_start_date_is_inclusive(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        _make_image(resp)

        today = timezone.now().date()
        tomorrow = today + datetime.timedelta(days=1)

        response = self.client.get(
            _response_images_url(org.id),
            {"start": today.isoformat(), "end": tomorrow.isoformat()},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    @authenticate
    def test_end_date_is_exclusive(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        _make_image(resp)

        today = timezone.now().date()

        # end = today means "before today midnight" — response created today should be excluded
        response = self.client.get(
            _response_images_url(org.id),
            {"start": "2020-01-01", "end": today.isoformat()},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 0)

    @authenticate
    def test_responses_outside_range_excluded(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        _make_image(resp)

        # Past date range — response created today should not appear
        response = self.client.get(
            _response_images_url(org.id),
            {"start": "2020-01-01", "end": "2020-06-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 0)

    @authenticate
    def test_pagination_limit_and_offset(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        for _ in range(3):
            _make_image(resp)

        response = self.client.get(
            _response_images_url(org.id),
            {"start": "2020-01-01", "end": "2030-01-01", "limit": "2", "offset": "0"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["next"])

    @authenticate
    def test_multiple_images_per_response(self):
        org = OrganisationFactory()
        MembershipFactory(user=authenticate.user, organisation=org, membership_type=MembershipType.ADMIN)
        survey = SurveyFactory(organisation=org)

        resp = ResponseFactory(survey=survey)
        img1 = _make_image(resp)
        img2 = _make_image(resp)

        response = self.client.get(_response_images_url(org.id), {"start": "2020-01-01", "end": "2030-01-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)
        ids = {r["id"] for r in data["results"]}
        self.assertEqual(ids, {img1.id, img2.id})
