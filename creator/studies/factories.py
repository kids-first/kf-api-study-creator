import pytz
import factory
import factory.fuzzy
from .models import Study


class StudyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Study

    kf_id = factory.fuzzy.FuzzyText(
                length=8,
                prefix='SD_',
                chars='ABCDEFGHIJKLMNOPQRSTVWXYZ1234567890'
            )
    name = factory.Faker('bs')
    created_at = factory.Faker('date_time_between',
                               start_date='-2y', end_date='now',
                               tzinfo=pytz.UTC)
    bucket = factory.Faker('slug')
