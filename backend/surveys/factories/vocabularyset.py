import factory

from surveys.models import VocabularySet


class VocabularySetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VocabularySet

    code = factory.Faker("lexify", text="????")
    name = factory.Faker("text", max_nb_chars=20)
    organisation = None
