import pytz
import factory
from creator.releases.models import Release, ReleaseTask, ReleaseService
from creator.users.factories import UserFactory


class ReleaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Release

    description = factory.Faker("paragraph", nb_sentences=3)
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )


class ReleaseTaskFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReleaseTask

    uuid = factory.Faker("uuid4")
    release = factory.SubFactory(ReleaseFactory)
    release_service = factory.SubFactory(
        "creator.releases.factories.ReleaseServiceFactory"
    )
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )


class ReleaseServiceFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReleaseService

    uuid = factory.Faker("uuid4")
    name = factory.Faker("bs")
    description = factory.Faker("paragraph", nb_sentences=3)
    url = factory.Faker("url")
    creator = factory.SubFactory(UserFactory)
    enabled = True
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
