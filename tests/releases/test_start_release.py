import pytest
from datetime import datetime
from graphql_relay import to_global_id

from creator.releases.models import Release, ReleaseTask
from creator.studies.factories import StudyFactory
from creator.releases.factories import ReleaseFactory, ReleaseServiceFactory


START_RELEASE = """
mutation ($input: StartReleaseInput!) {
    startRelease(input: $input) {
        release {
            id
            state
            name
            description
            isMajor
            studies {
                edges {
                    node {
                        id
                        kfId
                    }
                }
            }
            tasks {
                edges {
                    node {
                        id
                        kfId
                        releaseService {
                            id
                            kfId
                        }
                    }
                }
            }
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
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_start_release(db, clients, mocker, user_group, allowed):
    """
    Test the start release mutation.
    """
    mock_rq = mocker.patch("creator.releases.mutations.django_rq.enqueue")

    client = clients.get(user_group)
    study = StudyFactory()
    service = ReleaseServiceFactory()

    variables = {
        "input": {
            "name": "Test Release",
            "description": "Test Release",
            "isMajor": False,
            "studies": [to_global_id("StudyNode", study.pk)],
            "services": [to_global_id("ReleaseServiceNode", service.pk)],
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": START_RELEASE, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        assert resp.json()["data"]["startRelease"]["release"] is not None
        release = resp.json()["data"]["startRelease"]["release"]
        assert release["state"] == "initializing"
        assert release["name"] == "Test Release"
        assert release["description"] == "Test Release"
        assert release["isMajor"] is False
        assert len(release["studies"]["edges"]) == 1
        assert release["studies"]["edges"][0]["node"]["kfId"] == study.pk
        assert ReleaseTask.objects.count() == 1
        assert len(release["tasks"]["edges"]) == 1
        assert (
            release["tasks"]["edges"][0]["node"]["releaseService"]["kfId"]
            == service.pk
        )
        assert mock_rq.call_count == 1
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_start_release_unknown_studies(db, clients):
    """
    Test that inclusion of unknown studies is not allowed
    """
    client = clients.get("Administrators")

    variables = {
        "input": {
            "name": "Test Release",
            "description": "Non existant study",
            "studies": [to_global_id("StudyNode", "SD_00000000")],
            "services": [],
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": START_RELEASE, "variables": variables},
        content_type="application/json",
    )

    assert (
        resp.json()["errors"][0]["message"]
        == "Study SD_00000000 does not exist"
    )


def test_start_release_unknown_service(db, clients):
    """
    Test that inclusion of unknown services is not allowed
    """
    client = clients.get("Administrators")

    variables = {
        "input": {
            "name": "Test Release",
            "description": "Non existant study",
            "studies": [],
            "services": [to_global_id("ReleaseServiceNode", "TS_00000000")],
        }
    }

    resp = client.post(
        "/graphql",
        data={"query": START_RELEASE, "variables": variables},
        content_type="application/json",
    )

    assert (
        resp.json()["errors"][0]["message"]
        == "Service TS_00000000 does not exist"
    )


def test_release_factory_ended_at(db):
    """
    Test so that codecov stops complaining about the ended_at post generation
    hook.
    """
    release = ReleaseFactory(ended_at=datetime.now())
    assert release.ended_at is not None
    release = ReleaseFactory.build()
    assert release.ended_at is None
