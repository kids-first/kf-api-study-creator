import pytz
import factory
import random
from faker.providers import BaseProvider
from .models import File, Object
from creator.studies.models import Study


class FileTypeProvider(BaseProvider):
    def file_type(self):
        return random.choice(['SAM', 'SHM', 'CLN', 'FAM'])


factory.Faker.add_provider(FileTypeProvider)


class ObjectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Object

    key = factory.Faker('file_name')
    size = factory.Faker('pyint')
    created_at = factory.Faker('date_time_between',
                               start_date='-2y', end_date='now',
                               tzinfo=pytz.UTC)


class FileFactory(factory.DjangoModelFactory):
    class Meta:
        model = File

    name = factory.Faker('file_name')
    description = factory.Faker('paragraph', nb_sentences=3)
    study = factory.Iterator(Study.objects.all())
    file_type = factory.Faker('file_type')

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        n = random.randint(1, 5)
        return ObjectFactory.create_batch(n, root_file=self)
