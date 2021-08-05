import pytz
import factory
import factory.fuzzy
from faker.providers import BaseProvider
from .models import Study
from creator.organizations.factories import OrganizationFactory
from creator.buckets.factories import BucketFactory
from creator.files.factories import FileFactory


class StudyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Study
        django_get_or_create = ("kf_id",)

    kf_id = factory.fuzzy.FuzzyText(
        length=8, prefix="SD_", chars="ABCDEFGHIJKLMNOPQRSTVWXYZ1234567890"
    )
    name = factory.Faker("bs")
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    bucket = factory.Faker("slug")
    external_id = factory.Faker("slug")

    buckets = factory.RelatedFactory(BucketFactory, "study")

    organization = factory.SubFactory(OrganizationFactory)

    @factory.post_generation
    def num_files(self, create, how_many, **kwargs):
        """
        After a Study is created with the factory, generate _how_many_
        Files that are a part of the Study. If _how_many_ is not provided,
        default to _DEFAULT_NUM_.
        """
        DEFAULT_NUM = 3
        if create:
            if how_many is None:
                how_many = DEFAULT_NUM
            for _ in range(how_many):
                FileFactory(study=self)
