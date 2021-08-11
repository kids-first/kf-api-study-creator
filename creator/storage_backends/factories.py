import factory
import pytz
from creator.organizations.factories import OrganizationFactory
from creator.storage_backends.models import StorageBackend


class StorageBackendFactory(factory.DjangoModelFactory):
    class Meta:
        model = StorageBackend

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    name = factory.Faker("bs")
    bucket = factory.Faker("slug")
    prefix = factory.Faker("uri_path")
    access_key = factory.Faker("password", special_chars=False)
    secret_key = factory.Faker("password", special_chars=False)
    organization = factory.SubFactory(OrganizationFactory)
