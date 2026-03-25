import factory

from organisations.factories import OrganisationFactory
from surveys.models import Survey
from surveys.surveytype import SurveyType
from users.factories import UserFactory


class SurveyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Survey

    title = factory.Faker("text", max_nb_chars=50)
    organisation = factory.SubFactory(OrganisationFactory)
    pole = None
    created_by = factory.SubFactory(UserFactory)
    survey_type = SurveyType.SELF_CONTAINED
    campaign = None
    json_schema = None
