import factory

from surveys.factories.placette import PlacetteFactory
from surveys.factories.placettelevel import PlacetteLevelFactory
from surveys.models import PlacetteNode


class PlacetteNodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlacetteNode

    placette = factory.SubFactory(PlacetteFactory)
    level = factory.SubFactory(PlacetteLevelFactory)
    parent = None
    label = factory.Faker("word")
    lat = None
    lon = None
