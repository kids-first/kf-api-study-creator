import pytz
import factory
import factory.fuzzy
import random
from faker.providers import BaseProvider
from .models import File, Version
from creator.studies.models import Study
from creator.users.factories import UserFactory


class FileTypeProvider(BaseProvider):
    def file_type(self):
        return random.choice(['SEQ', 'SHM', 'CLN', 'OTH'])


factory.Faker.add_provider(FileTypeProvider)


class VersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Version

    kf_id = factory.fuzzy.FuzzyText(
                length=8,
                prefix='FV_',
                chars='ABCDEFGHIJKLMNOPQRSTVWXYZ1234567890'
            )
    key = factory.Faker('file_name')
    size = factory.Faker('pyint')
    description = factory.Faker('paragraph', nb_sentences=3)
    created_at = factory.Faker('date_time_between',
                               start_date='-2y', end_date='now',
                               tzinfo=pytz.UTC)

    creator = factory.SubFactory(UserFactory)

    file_name = factory.Faker('file_name')

class FileFactory(factory.DjangoModelFactory):
    class Meta:
        model = File

    kf_id = factory.fuzzy.FuzzyText(
                length=8,
                prefix='SF_',
                chars='ABCDEFGHIJKLMNOPQRSTVWXYZ1234567890'
            )
    name = factory.Faker('file_name')
    description = factory.Faker('paragraph', nb_sentences=3)
    study = factory.Iterator(Study.objects.all())
    file_type = factory.Faker('file_type')
    creator = factory.SubFactory(UserFactory)

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        n = random.randint(1, 5)
        return VersionFactory.create_batch(n, root_file=self)
