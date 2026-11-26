import factory

from surveys.models import Placette


class PlacetteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Placette

    label = factory.Faker("text", max_nb_chars=50)
    lat = factory.Faker("latitude")
    lon = factory.Faker("longitude")
    characteristics = factory.LazyFunction(dict)
    survey = factory.SubFactory("surveys.factories.placettesurvey.PlacetteSurveyFactory")
