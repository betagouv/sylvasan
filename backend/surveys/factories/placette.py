import factory

from surveys.models import Placette


class PlacetteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Placette

    label = factory.Faker("text", max_nb_chars=50)
    lat = factory.Faker("latitude")
    lon = factory.Faker("longitude")
    characteristics = factory.LazyFunction(dict)

    @factory.post_generation
    def surveys(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for survey in extracted:
                self.surveys.add(survey)
        else:
            from surveys.factories.placettesurvey import PlacetteSurveyFactory

            self.surveys.add(PlacetteSurveyFactory())
