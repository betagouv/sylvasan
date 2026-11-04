import factory
from organisations.factories import OrganisationFactory

from surveys.models import PlacetteSurvey


class PlacetteSurveyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlacetteSurvey

    name = factory.Faker("text", max_nb_chars=50)
    organisation = factory.SubFactory(OrganisationFactory)
    pole = None
    is_published = True
