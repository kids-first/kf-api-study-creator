import pytz
import factory
import factory.fuzzy
from faker.providers import BaseProvider
from .models import Study
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

    organization = factory.SubFactory(
        "creator.organizations.factories.OrganizationFactory", studies=0
    )
    buckets = factory.RelatedFactory(
        BucketFactory, "study", organization=organization
    )

    @factory.post_generation
    def files(self, create, extracted, **kwargs):
        """
        After a Study is created with the factory, generate _extracted_
        Files that are a part of the Study. If _extracted_ is not provided,
        default to _DEFAULT_NUM_.
        """
        DEFAULT_NUM = 5
        if not create:
            return
        extracted = DEFAULT_NUM if extracted is None else extracted
        if extracted:
            FileFactory.create_batch(extracted, study=self)
