import pytest
from graphql_relay import to_global_id
from django.core.exceptions import ValidationError

from creator.releases.factories import ReleaseServiceFactory

CREATE_RELEASE_SERVICE = """
mutation ($input: CreateReleaseServiceInput!) {
    createReleaseService(input: $input) {
        releaseService {
            id
            kfId
            name
            description
            url
            enabled
        }
    }
}
"""

UPDATE_RELEASE_SERVICE = """
mutation ($id: ID!, $input: UpdateReleaseServiceInput!) {
    updateReleaseService(id: $id, input: $input) {
        releaseService {
            id
            kfId
            name
            description
            url
            enabled
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
def test_create_release_service(db, clients, mocker, user_group, allowed):
    """
    Test the create mutation.
    """
    mock = mocker.patch("creator.releases.mutations.validate_endpoint")
    mock.return_value = None

    client = clients.get(user_group)

    variables = {
        "name": "test service",
        "description": "Hello world",
        "url": "http://testservice",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_RELEASE_SERVICE,
            "variables": {"input": variables},
        },
        content_type="application/json",
    )

    if allowed:
        service = resp.json()["data"]["createReleaseService"]["releaseService"]
        assert service is not None
        assert service["enabled"] is True
        assert service["name"] == "test service"
        assert service["description"] == "Hello world"
        assert service["url"] == "http://testservice"
        assert mock.call_count == 1
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
def test_update_release_service(db, clients, user_group, allowed):
    """
    Test the update mutation.
    """
    client = clients.get(user_group)

    release_service = ReleaseServiceFactory(enabled=False)

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_RELEASE_SERVICE,
            "variables": {
                "id": to_global_id("ReleaseServiceNode", release_service.pk),
                "input": {"name": "test", "enabled": True},
            },
        },
        content_type="application/json",
    )

    if allowed:
        service = resp.json()["data"]["updateReleaseService"]["releaseService"]
        assert service is not None
        assert service["enabled"] is True
        assert service["name"] == "test"
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


def test_update_release_service_does_not_exist(db, clients):
    """
    Test that a service that does not exist can't be updated
    """
    client = clients.get("Administrators")

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_RELEASE_SERVICE,
            "variables": {
                "id": to_global_id("ReleaseServiceNode", "ABC"),
                "input": {"name": "test", "enabled": True},
            },
        },
        content_type="application/json",
    )

    assert (
        resp.json()["errors"][0]["message"]
        == "Release Service ABC does not exist"
    )


def test_create_release_service_bad_url(db, clients, mocker):
    """
    Test the create mutation fails if the url is invalid
    """
    mock = mocker.patch("creator.releases.mutations.validate_endpoint")
    mock.side_effect = ValidationError("bad response")

    client = clients.get("Administrators")

    variables = {
        "name": "test service",
        "description": "Hello world",
        "url": "http://testservice",
    }
    resp = client.post(
        "/graphql",
        data={
            "query": CREATE_RELEASE_SERVICE,
            "variables": {"input": variables},
        },
        content_type="application/json",
    )

    assert "errors" in resp.json()
    assert (
        "problem with the provided URL" in resp.json()["errors"][0]["message"]
    )
