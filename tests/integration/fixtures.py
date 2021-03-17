import os
import pytest

from creator.studies.data_generator.study_generator import (
    StudyGenerator,
    delete_entities,
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
