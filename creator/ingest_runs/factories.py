import pytz
import factory
from creator.ingest_runs.models import IngestRun


class IngestRunFactory(factory.DjangoModelFactory):
    class Meta:
        model = IngestRun

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
