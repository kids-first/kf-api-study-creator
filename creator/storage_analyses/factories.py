import pytz
import factory
import factory.fuzzy

from creator.storage_analyses.models import AuditState, ExpectedFile
from creator.studies.factories import StudyFactory


class ExpectedFileFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpectedFile

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    file_location = factory.Faker("name")
    size = factory.Faker("pyint")
    hash = factory.Faker("name")
    hash_algorithm = factory.fuzzy.FuzzyChoice(
        ["MD5", "SHA256", "CRC32", "SHA512"]
    )
    audit_state = factory.fuzzy.FuzzyChoice(
        [
            attr for attr in dir(AuditState)
            if not callable(getattr(AuditState, attr))
            and not attr.startswith("__")
        ]
    )
    study = factory.SubFactory(StudyFactory)
