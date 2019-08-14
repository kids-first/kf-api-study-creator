import pytest
import pytz
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import (
    sync_cavatica_projects,
    sync_cavatica_account,
)
from creator.studies.models import Study
from creator.projects.models import Project


SYNC_PROJECTS_MUTATION = """
mutation syncProjects {
    syncProjects {
        updated {
            edges {
                node {
                    projectId
                }
            }
        }
        created {
            edges {
                node {
                    projectId
                }
            }
        }
    }
}
"""


@pytest.fixture
def mock_sync_cavatica_account(mocker):
    """ Mocks out sync Cavatica account functions """
    sync_cavatica_account = mocker.patch(
        "creator.projects.cavatica.sync_cavatica_account"
    )
    sync_cavatica_account.return_value = [], []
    return sync_cavatica_account


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

    Api = MagicMock()
    Api().projects = ProjectMock

    sbg.Api = Api

    return sbg


def test_correct_sync(db, mock_sync_cavatica_account):

    sync_cavatica_projects()

    assert mock_sync_cavatica_account.call_count == 2

    mock_sync_cavatica_account.assert_any_call("HAR")
    mock_sync_cavatica_account.assert_any_call("DEL")


def test_sync_projects(db, mock_cavatica_api):

    sync_cavatica_account("HAR")

    # Checking if the api is constructed with the correct settings
    mock_cavatica_api.Api.assert_called_with(
        url="https://cavatica-api.sbgenomics.com/v2", token=None
    )
    assert len(mock_cavatica_api.Api().projects.query().all()) == 2

    assert Project.objects.count() == 2
    assert Project.objects.first().project_type == "HAR"

    cavatica_project = mock_cavatica_api.Api().projects.query().all()[0]
    project = Project.objects.first()

    # Check if the fields are copied correctly
    assert project.url == cavatica_project.href
    assert project.project_id == cavatica_project.id

    for field in [
        "name",
        "description",
        "created_by",
        "created_on",
        "modified_on",
    ]:
        assert getattr(cavatica_project, field) == getattr(project, field)


def test_sync_mutation(db, mocker, admin_client, settings):
    """
    Test that the sync_projects mutation is called correctly
    """
    sbg = mocker.patch("creator.projects.cavatica.sbg")

    # Project subresource of the sbg api
    ProjectMock = MagicMock()
    project_list = [
        CavaticaProject(id="test_id_01_harmonization"),
        CavaticaProject(id="test_id_02_harmonization"),
    ]
    ProjectMock.query().all.return_value = project_list

    Api = MagicMock()
    Api().projects = ProjectMock

    sbg.Api = Api

    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": SYNC_PROJECTS_MUTATION},
    )

    assert len(resp.json()["data"]["syncProjects"]["created"]["edges"]) == 2

    project_list = [
        CavaticaProject(
            id="test_id_01_harmonization",
            description="New description",
            modified_on=datetime(2018, 11, 4, 15, 16, 17, 0, tzinfo=pytz.utc),
        ),
        CavaticaProject(id="test_id_02_harmonization"),
        CavaticaProject(id="test_id_03_harmonization"),
    ]

    sbg.Api().projects.query().all.return_value = project_list

    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": SYNC_PROJECTS_MUTATION},
    )

    assert len(resp.json()["data"]["syncProjects"]["created"]["edges"]) == 1
    assert len(resp.json()["data"]["syncProjects"]["updated"]["edges"]) == 1
