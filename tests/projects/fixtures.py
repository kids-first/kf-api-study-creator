import pytest
import pytz
from typing import Callable
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CavaticaProject:
    id: str = "author/test-harmonization"
    name: str = "Test name-bwa-mem"
    description: str = "Test description"
    href: str = "test_url"
    created_by: str = "author"
    created_on: datetime = datetime(
        2018, 8, 13, 15, 16, 17, 0, tzinfo=pytz.utc
    )
    modified_on: datetime = datetime(
        2018, 10, 13, 15, 16, 17, 0, tzinfo=pytz.utc
    )
    save: Callable = MagicMock()


@pytest.fixture
def mock_cavatica_api(mocker):
    """ Mocks out api for creating Cavatica project functions """

    sbg = mocker.patch("creator.projects.cavatica.sbg")

    # Project subresource of the sbg api
    ProjectMock = MagicMock()
    project_list = [
        CavaticaProject(id="test_id_01_harmonization"),
        CavaticaProject(id="test_id_02_harmonization"),
    ]
    ProjectMock.query().all.return_value = project_list
    ProjectMock.create.return_value = CavaticaProject()

    Api = MagicMock()
    Api().projects = ProjectMock

    sbg.Api = Api

    return sbg
