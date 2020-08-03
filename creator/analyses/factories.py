import pytz
import factory
import factory.fuzzy
from creator.analyses.models import Analysis
from creator.files.models import Version
from creator.users.factories import UserFactory


class AnalysisFactory(factory.DjangoModelFactory):
    class Meta:
        model = Analysis
        django_get_or_create = ("version",)

    id = factory.Sequence(lambda n: n)
    known_format = factory.Faker("boolean")

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    creator = factory.SubFactory(UserFactory)
    version = factory.Iterator(Version.objects.all())
