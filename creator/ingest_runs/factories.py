import pytz
import factory
from creator.ingest_runs.models import (
    IngestRun,
    ValidationRun,
    ValidationResultset,
)
from creator.data_reviews.factories import DataReviewFactory
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


class ValidationRunFactory(factory.DjangoModelFactory):
    class Meta:
        model = ValidationRun

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    success = factory.fuzzy.FuzzyChoice([True, False])
    progress = factory.fuzzy.FuzzyFloat(0, 1)
    creator = factory.SubFactory(UserFactory)
    data_review = factory.SubFactory(DataReviewFactory)

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for version in extracted:
                self.versions.add(version)


class ValidationResultsetFactory(factory.DjangoModelFactory):
    class Meta:
        model = ValidationResultset

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    failed = factory.fuzzy.FuzzyInteger(0, 50)
    passed = factory.fuzzy.FuzzyInteger(0, 50)
    did_not_run = factory.fuzzy.FuzzyInteger(0, 50)
    data_review = factory.SubFactory(DataReviewFactory)
