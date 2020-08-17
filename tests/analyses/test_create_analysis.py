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
from creator.analyses.models import Analysis


CREATE_PROJECT_MUTATION = """
mutation runAnalysis($version: ID!) {
    createAnalysis(version: $version) {
        analysis {
            creator {
                username
            }
            version {
                fileName
            }
            columns
            knownFormat
        }
    }
}
"""


@pytest.fixture
def clinical_file(upload_file, clients):
    client = clients.get("Services")

    study = StudyFactory()
    resp = upload_file(
        study.kf_id, "SD_ME0WME0W/FV_4DP2P2Y2_clinical.tsv", client=client
    )

    file_id = resp.json()["data"]["createFile"]["file"]["id"]
    version_id = resp.json()["data"]["createFile"]["file"]["versions"][
        "edges"
    ][0]["node"]["id"]

    return file_id, version_id


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
def test_create_analysis_mutation(
    db, clients, clinical_file, user_group, allowed
):
    """
    Test that analyses are properly controlled be permissions
    """
    study = StudyFactory(kf_id="SD_00000000")
    study.save()

    _, version_id = clinical_file

    client = clients.get(user_group)
    kf_id = to_global_id("StudyNode", "SD_00000000")
    variables = {"version": version_id}

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_PROJECT_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["createAnalysis"]["analysis"]
        resp_body = (
            resp.json()["data"]["createAnalysis"]["analysis"]["knownFormat"]
            is True
        )
        assert Analysis.objects.count() == 1
    else:
        assert Analysis.objects.count() == 0
        assert resp.json()["errors"][0]["message"] == "Not allowed"
