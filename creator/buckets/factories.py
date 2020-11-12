import pytz
import factory
from faker.providers import BaseProvider
from .models import Bucket, BucketInventory


class BucketFactory(factory.DjangoModelFactory):
    class Meta:
        model = Bucket
        django_get_or_create = ("name",)

    name = factory.Faker("slug")
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )

    @factory.post_generation
    def inventories(obj, create, extracted=5, **kwargs):
        if not create:
            return

        if extracted:
            if not isinstance(extracted, int):
                extracted = 5

            BucketInventoryFactory.create_batch(
                extracted, bucket__name=obj.name, **kwargs
            )


class SummaryProvider(BaseProvider):
    def summary(self):
        return {
            "size": {
                "total": self.random_int(max=10 ** 15),
                "by_file_format": {
                    "bam": self.random_int(max=10 ** 11),
                    "bai": self.random_int(max=10 ** 11),
                    "cram": self.random_int(max=10 ** 11),
                    "crai": self.random_int(max=10 ** 11),
                    "txt": self.random_int(max=10 ** 5),
                    "vcf": self.random_int(max=10 ** 7),
                    "gvcf": self.random_int(max=10 ** 7),
                },
                "by_state": {
                    "latest": self.random_int(max=10 ** 7),
                    "deleted": self.random_int(max=10 ** 7),
                },
            },
            "count": {
                "total": self.random_int(max=10 ** 7),
                "by_file_format": {
                    "bam": self.random_int(max=10 ** 4),
                    "bai": self.random_int(max=10 ** 4),
                    "cram": self.random_int(max=10 ** 4),
                    "crai": self.random_int(max=10 ** 4),
                    "txt": self.random_int(max=10 ** 2),
                    "vcf": self.random_int(max=10 ** 3),
                    "gvcf": self.random_int(max=10 ** 4),
                },
                "latest": self.random_int(max=10 ** 5),
                "deleted": self.random_int(max=10 ** 4),
            },
        }


factory.Faker.add_provider(SummaryProvider)


class BucketInventoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = BucketInventory
        django_get_or_create = ("id",)

    id = factory.Faker("uuid4")
    bucket = factory.SubFactory(BucketFactory)
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    total_bytes = factory.Faker("pyint", max_value=10 ** 12)

    summary = factory.Faker("summary")
