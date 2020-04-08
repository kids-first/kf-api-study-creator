import pytest
from creator.files.models import Version
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory


update_query = """
mutation (
    $kfId:String!,
    $state: VersionState!,
    $description: String!,
) {
    updateVersion(
        kfId: $kfId,
        description: $description
        state: $state
    ) {
        version { id kfId state description size }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_update_version_auth(db, clients, versions, user_group, allowed):
    """
    Test that versions may bu updated only by admin or owners.
    """
    client = clients.get(user_group)
    study, file, version = versions

    query = update_query
    variables = {
        "kfId": version.kf_id,
        "description": "New description",
        "state": "PEN",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The operation should be successful
    if allowed:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["description"]
            == "New description"
        )
        version = Version.objects.get(kf_id=version.kf_id)
        assert version.description == "New description"
    # Should not be successful
    else:
        assert resp.status_code == 200
        assert resp.json()["data"]["updateVersion"] is None
        expected_error = "Not allowed"
        assert resp.json()["errors"][0]["message"] == expected_error


@pytest.mark.parametrize(
    "state,expected",
    [
        ("PEN", True),
        ("APP", True),
        ("CHN", True),
        ("PRC", True),
        ("OTH", 'Variable "$state" got invalid value'),
        ("XXX", 'Variable "$state" got invalid value'),
        ("Approved", 'Variable "$state" got invalid value'),
        (None, 'required type "VersionState!" was not provided'),
    ],
)
def test_update_state(db, clients, versions, state, expected):
    """
    Test that only valid states may be set.

    :state: Value to pass as the state field
    :expected: True if expected to pass, substring of the error message if
        it's expected to fail
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = update_query
    variables = {"kfId": version.kf_id, "description": "Test", "state": state}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The state is valid
    if expected is True:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["state"] == state
        )
        version = Version.objects.get(kf_id=version.kf_id)
        assert version.state == state
    # State is not known
    else:
        assert resp.status_code == 400
        assert expected in resp.json()["errors"][0]["message"]
        version = Version.objects.get(kf_id=version.kf_id)
