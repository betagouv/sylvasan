import factory

from surveys.factories.placettesurvey import PlacetteSurveyFactory
from surveys.models import PlacetteLevel


class PlacetteLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlacetteLevel

    placette_survey = factory.SubFactory(PlacetteSurveyFactory)
    parent_level = None
    name = factory.Faker("word")
    json_schema = None
    has_coordinates = False
    min_instances = None
    max_instances = None
    order = factory.Sequence(lambda n: n)
