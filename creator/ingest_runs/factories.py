import pytz
import factory
from creator.ingest_runs.models import IngestRun
from creator.users.factories import UserFactory


class IngestRunFactory(factory.DjangoModelFactory):
    class Meta:
        model = IngestRun

    name = factory.Faker("name")
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    creator = factory.SubFactory(UserFactory)

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for version in extracted:
                self.versions.add(version)
