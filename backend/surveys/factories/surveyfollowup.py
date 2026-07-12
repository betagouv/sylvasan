import factory
from organisations.factories import OrganisationFactory
from users.factories import UserFactory

from surveys.models import SurveyFollowUp

from .survey import SurveyFactory


class SurveyFollowUpFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SurveyFollowUp

    title = factory.Faker("text", max_nb_chars=50)
    organisation = factory.SubFactory(OrganisationFactory)
    parent_survey = factory.SubFactory(SurveyFactory)
    pole = None
    created_by = factory.SubFactory(UserFactory)
    json_schema = None
