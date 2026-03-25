import factory

from organisations.factories import OrganisationFactory
from surveys.models import Campaign


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    title = factory.Faker("text", max_nb_chars=50)
    organisation = factory.SubFactory(OrganisationFactory)
    pole = None
    start_date = None
    end_date = None
