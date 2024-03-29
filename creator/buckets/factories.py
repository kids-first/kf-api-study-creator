import pytz
import factory
from .models import Bucket
from creator.organizations.factories import OrganizationFactory


class BucketFactory(factory.DjangoModelFactory):
    class Meta:
        model = Bucket
        django_get_or_create = ('name',)

    name = factory.Faker("bs")
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    organization = factory.SubFactory(OrganizationFactory)
