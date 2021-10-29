import pytz
import factory
from creator.studies.factories import StudyFactory
from creator.storage_analyses.models import StorageAnalysis



class StorageAnalysisFactory(factory.DjangoModelFactory):
    class Meta:
        model = StorageAnalysis

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="-1d", tzinfo=pytz.UTC
    )
    study = factory.SubFactory(StudyFactory)
