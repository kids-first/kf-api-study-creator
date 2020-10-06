import pytz
import factory
from creator.releases.models import Release


class ReleaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Release

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
