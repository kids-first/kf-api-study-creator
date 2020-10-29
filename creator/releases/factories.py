import pytz
import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from creator.releases.models import Release, ReleaseTask, ReleaseService
from creator.studies.models import Study
from creator.users.factories import UserFactory

User = get_user_model()


class ReleaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Release

    name = factory.Faker("bs")
    description = factory.Faker("paragraph", nb_sentences=3)
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    state = factory.fuzzy.FuzzyChoice(
        ["staged", "published", "canceled", "failed"]
    )

    creator = factory.SubFactory(UserFactory)

    @factory.post_generation
    def studies(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.studies.set(extracted)
        else:
            # Add up to three studies to the release
            studies = Study.objects.all()
            studies = list(studies) + [None]
            studies = set(
                factory.fuzzy.FuzzyChoice(studies).fuzz() for _ in range(3)
            )
            studies = {study for study in studies if study is not None}
            self.studies.set(studies)

    @factory.post_generation
    def tasks(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.tasks.set(extracted)
        else:
            # Invoke tasks for up to three services
            services = ReleaseService.objects.all()
            services = list(services) + [None]
            services = set(
                factory.fuzzy.FuzzyChoice(services).fuzz() for _ in range(3)
            )
            services = {service for service in services if service is not None}

            for service in services:
                task = ReleaseTaskFactory(
                    release=self, release_service=service
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
