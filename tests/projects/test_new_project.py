import pytest
import pytz
import sevenbridges as sbg
from graphql_relay import to_global_id
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import (
    setup_cavatica,
    create_project,
    copy_users,
)
from creator.studies.factories import StudyFactory
from creator.projects.models import Project


CREATE_PROJECT_MUTATION = """
mutation newProject($input: ProjectInput!) {
    createProject(input: $input) {
        project {
            projectId
            name
            description
            createdOn
            modifiedOn
            workflowType
        }
    }
}
"""


@pytest.fixture(autouse=True)
def enable_projects(settings):
    settings.FEAT_CAVATICA_CREATE_PROJECTS = True
    settings.CAVATICA_HARMONIZATION_TOKEN = "abc"


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
def test_create_project_mutation(
    db, clients, mock_cavatica_api, user_group, allowed
):
    """
    Test that correct users may create Cavatica projects
    """
    study = StudyFactory(kf_id="SD_00000000")
    study.save()

    client = clients.get(user_group)
    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {
        "input": {"workflowType": "rsem", "study": kf_id, "projectType": "HAR"}
    }

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["createProject"]["project"]
        assert resp_body["workflowType"] == "rsem"
        assert Project.objects.count() == 1
        assert Project.objects.first().workflow_type == "rsem"
    else:
        assert Project.objects.count() == 0
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_create_project_study_does_not_exist(db, clients):
    """
    Test that a project may not be created when a study is not valid
    """
    client = clients.get("Administrators")

    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {
        "input": {"workflowType": "rsem", "study": kf_id, "projectType": "HAR"}
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("Study does not")
    assert Project.objects.count() == 0


def test_create_project_no_duplicate_workflows(db, clients, mock_cavatica_api):
    """
    Test that multiple projects with the same workflow may not be created for
    the same study.
    """
    client = clients.get("Administrators")

    study = StudyFactory(kf_id="SD_00000000")
    study.save()

    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {
        "input": {"workflowType": "rsem", "study": kf_id, "projectType": "HAR"}
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("Study already has")
    assert Project.objects.count() == 1


def test_create_project_invalid_workflows(db, clients, mock_cavatica_api):
    """
    Test that research projects with invalid workflow input may not be created.
    """
    client = clients.get("Administrators")

    study = StudyFactory(kf_id="SD_00000000")
    study.save()

    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {
        "input": {
            "workflowType": "invalid@workflow*input",
            "study": kf_id,
            "projectType": "RES",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("No special")
    assert Project.objects.count() == 0
