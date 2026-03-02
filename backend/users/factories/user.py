import random
import string

import factory
from django.contrib.auth import get_user_model


def _make_username():
    suffix = "".join(random.choice(string.ascii_letters) for _ in range(10))
    return "user_" + suffix


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    username = factory.LazyFunction(_make_username)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
        return manager.create_user(*args, **kwargs)
        return manager.create_user(*args, **kwargs)
        return manager.create_user(*args, **kwargs)
