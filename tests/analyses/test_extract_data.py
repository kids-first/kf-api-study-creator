import pytest
from graphql import GraphQLError
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory
from creator.files.models import Version
from creator.analyses.analyzer import extract_data


def test_extract_data_no_study(db, settings):
    settings.DEFAULT_FILE_STORAGE = "django_s3_storage.storage.S3Storage"

    version = Version()
    version.key.name = "test.csv"

    with pytest.raises(GraphQLError) as err:
        extract_data(version)
