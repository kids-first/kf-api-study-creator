import os
import pytest

from creator.ingest_runs.data_generator.study_generator import (
    delete_entities,
    StudyGenerator
)
LOCAL_DATASERVICE_URL = "http://localhost:5000"


@pytest.fixture
def test_study_generator(tmpdir):
    class TestStudyGenerator(StudyGenerator):
        """
        StudyGenerator for integration tests
        Ensures we are always using Data Service at localhost
        Uses temp dir for working dir
        """

        def __init__(self, *args, **kwargs):
            kwargs["working_dir"] = os.path.join(tmpdir, "output")
            super().__init__(*args, **kwargs)
            self.dataservice_url = LOCAL_DATASERVICE_URL

    return TestStudyGenerator


@pytest.fixture
def dataservice_setup():
    """
    Delete all data in Data Service before and after tests
    """
    delete_entities(LOCAL_DATASERVICE_URL)
    yield
    delete_entities(LOCAL_DATASERVICE_URL)
