import pytest
import pytz
from graphql_relay import to_global_id
from unittest.mock import MagicMock
from datetime import datetime
from creator.projects.cavatica import (
    sync_cavatica_projects,
    sync_cavatica_account,
)
from creator.studies.models import Study

from creator.projects.models import Project
from creator.projects.factories import ProjectFactory

from creator.events.models import Event
from tests.projects.fixtures import CavaticaProject


IMPORT_FILES_MUTATION = """
mutation ImportVolumeFiles($project: ID!) {
    importVolumeFiles(project: $project) {
        project {
            projectId
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_import_files(db, mocker, clients, user_group, allowed):
    """
    Test that the correct users may import files
    """
    client = clients.get(user_group)

    project = ProjectFactory()

    import_volume = mocker.patch("creator.tasks.import_volume_files")

    resp = client.post(
        "/graphql",
        data={
            "query": IMPORT_FILES_MUTATION,
            "variables": {
                "project": to_global_id("ProjectNode", project.project_id)
            },
        },
        content_type="application/json",
    )

    if allowed:
        assert import_volume.call_count == 1
        assert (
            resp.json()["data"]["importVolumeFiles"]["project"]["projectId"]
            == project.project_id
        )
    else:
        assert import_volume.call_count == 0
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_import_files_events(db, clients, mocker):
    """
    Test that the correct events are emitted
    """
    client = clients.get("Administrators")

    project = ProjectFactory()

    import_volume = mocker.patch("creator.tasks.import_volume_files")

    assert Event.objects.count() == 0

    resp = client.post(
        "/graphql",
        data={
            "query": IMPORT_FILES_MUTATION,
            "variables": {
                "project": to_global_id("ProjectNode", project.project_id)
            },
        },
        content_type="application/json",
    )

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="IM_STR").count() == 1
    assert Event.objects.filter(event_type="IM_SUC").count() == 1


def test_import_files_no_project(db, clients, mocker):
    """
    Test that error is raised if project does not exist and the import task
    is never scheduled
    """
    client = clients.get("Administrators")

    import_volume = mocker.patch("creator.tasks.import_volume_files")

    resp = client.post(
        "/graphql",
        data={
            "query": IMPORT_FILES_MUTATION,
            "variables": {"project": to_global_id("ProjectNode", "ABC")},
        },
        content_type="application/json",
    )

    assert Event.objects.count() == 0
    assert "errors" in resp.json()
