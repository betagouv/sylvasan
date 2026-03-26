import factory

from organisations.models import Organisation


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    name = factory.Faker("lexify", text="?????")
