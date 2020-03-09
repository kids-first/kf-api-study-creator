import pytz
import factory
import random
from .models import Bucket


class BucketFactory(factory.DjangoModelFactory):
    class Meta:
        model = Bucket

    name = factory.Faker("bs")
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
