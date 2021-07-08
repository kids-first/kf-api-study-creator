import pytz
import factory
import factory.fuzzy
from faker.providers import BaseProvider
from .models import File, Version
from creator.studies.factories import StudyFactory
from creator.users.factories import UserFactory


class FuzzyTags(factory.fuzzy.BaseFuzzyAttribute):
    def __init__(self, tags):
        self.tags = set(tags)

    def fuzz(self):
        sorted_tags = sorted(list(self.tags))
        n = factory.fuzzy.FuzzyInteger(0, 4).fuzz()
        tags = set()
        for _ in range(n):
            i = factory.fuzzy.FuzzyInteger(0, len(self.tags) - 1).fuzz()
            tags.add(sorted_tags[i])
        return list(tags)


class FileTypeProvider(BaseProvider):
    def file_type(self):
        return factory.fuzzy.FuzzyChoice(["SEQ", "OTH"]).fuzz()

    def version_state(self):
        n = factory.fuzzy.FuzzyInteger(1, 5).fuzz()
        return factory.fuzzy.FuzzyChoice(["PEN", "PRC", "CHN", "APP"]).fuzz()

    def tags(self):
        return FuzzyTags(
            ["dbGaP", "DCC", "Email", "Data Dictionary", "Batch 1", "Batch 2"]
        ).fuzz()


factory.Faker.add_provider(FileTypeProvider)


class VersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Version
        django_get_or_create = ("kf_id",)

    kf_id = factory.Sequence(lambda n: f"FV_{n:0>8}")

    key = factory.Faker("file_name")
    size = factory.Faker("pyint")
    description = factory.Faker("paragraph", nb_sentences=3)
    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )

    creator = factory.SubFactory(UserFactory)

    file_name = factory.Faker("file_name")
    state = factory.Faker("version_state")
    root_file = factory.SubFactory("creator.files.factories.FileFactory")


class FileFactory(factory.DjangoModelFactory):
    class Meta:
        model = File
        django_get_or_create = ("kf_id",)

    kf_id = factory.Sequence(lambda n: f"SF_{n:0>8}")
    name = factory.Faker("file_name")
    description = factory.Faker("paragraph", nb_sentences=3)
    study = factory.SubFactory(StudyFactory)
    file_type = factory.Faker("file_type")
    creator = factory.SubFactory(UserFactory)
    tags = factory.Faker("tags")

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        n = factory.fuzzy.FuzzyInteger(1, 5).fuzz()
        return VersionFactory.create_batch(n, root_file=self)
