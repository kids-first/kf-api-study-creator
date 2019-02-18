import factory
import random
from .models import FileEssence, Object
from creator.studies.models import Study


class ObjectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Object 

    key = factory.Faker('file_path', depth=3)
    version_id = factory.Faker('md5')


class FileEssenceFactory(factory.DjangoModelFactory):
    class Meta:
        model = FileEssence

    name = factory.Faker('file_name')
    description = factory.Faker('paragraph', nb_sentences=3)
    study = factory.Iterator(Study.objects.all())

    @factory.post_generation
    def versions(self, create, extracted, **kwargs):
        n = random.randint(1,5)
        return ObjectFactory.create_batch(n, root_file=self)
