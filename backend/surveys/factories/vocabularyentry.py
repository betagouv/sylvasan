import factory

from surveys.models import VocabularyEntry

from .vocabularyset import VocabularySetFactory


class VocabularyEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VocabularyEntry

    vocabulary_set = factory.SubFactory(VocabularySetFactory)
    code = factory.Faker("lexify", text="????")
    label = factory.Faker("text", max_nb_chars=50)
    position = None
