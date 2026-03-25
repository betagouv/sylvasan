import factory

from responses.models import Response, ResponseStatus
from surveys.factories import SurveyFactory
from users.factories import UserFactory


class ResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Response

    survey = factory.SubFactory(SurveyFactory)
    respondant = factory.SubFactory(UserFactory)
    status = ResponseStatus.DRAFT
    data = factory.LazyFunction(dict)
    context = None
    submission_date = None
