import pytest
import pytz
from unittest.mock import MagicMock
from datetime import datetime
from creator.projects.cavatica import (
    sync_cavatica_projects,
    sync_cavatica_account,
)
from creator.studies.models import Study
from creator.projects.models import Project
from creator.events.models import Event
from tests.projects.fixtures import CavaticaProject


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
    sync_cavatica_account.return_value = [], [], []
    return sync_cavatica_account


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


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_sync_mutation(db, mocker, clients, user_group, allowed):
    """
    Test that the correct users may sync projects
    """

    client = clients.get(user_group)

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

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": SYNC_PROJECTS_MUTATION},
    )

    if not allowed:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        return

    assert len(resp.json()["data"]["syncProjects"]["created"]["edges"]) == 2
    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="PR_CRE").count() == 2

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

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": SYNC_PROJECTS_MUTATION},
    )

    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="PR_CRE").count() == 3
    assert Event.objects.filter(event_type="PR_UPD").count() == 1

    assert len(resp.json()["data"]["syncProjects"]["created"]["edges"]) == 1
    assert len(resp.json()["data"]["syncProjects"]["updated"]["edges"]) == 1
