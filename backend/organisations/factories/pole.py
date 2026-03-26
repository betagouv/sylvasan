import factory

from organisations.models import Pole

from .organisation import OrganisationFactory


class PoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pole

    name = factory.Faker("text", max_nb_chars=20)
    organisation = factory.SubFactory(OrganisationFactory)
