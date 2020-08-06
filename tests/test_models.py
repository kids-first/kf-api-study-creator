import pytest
import uuid

from creator.studies.models import Study
from creator.files.models import File, Version, DownloadToken
from creator.projects.models import Project


@pytest.mark.parametrize(
    "model,expected",
    [
        (Study, "SD_00000001"),
        (File, "SF_00000001"),
        (Version, "FV_00000001"),
        (Project, "test/test"),
    ],
)
def test_str(model, expected):
    """ Test string conversion functions """
    obj = model(pk=expected)
    assert str(obj) == expected
