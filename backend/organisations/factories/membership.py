import factory

from organisations.models import Membership, MembershipType
from users.factories import UserFactory

from .organisation import OrganisationFactory


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    pole = None
    membership_type = MembershipType.RESPONDER
