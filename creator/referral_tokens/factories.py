import pytz
import factory
from .models import ReferralToken


class ReferralTokenFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReferralToken
        django_get_or_create = ("uuid",)

    uuid = factory.Faker("uuid4")
    email = factory.Faker("email")
    created_at = factory.Faker(
        "date_time_between", start_date="-2d", end_date="now", tzinfo=pytz.UTC
    )
