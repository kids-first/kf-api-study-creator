import pytest
from creator.files.models import Version


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
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("admin", False, True),
        ("service", True, True),
        ("service", False, True),
        ("user", True, True),
        ("user", False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_update_version_auth(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    prep_file,
    user_type,
    authorized,
    expected,
):
    """
    Test that versions may bu updated only by admin or owners.
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    study_id, file_id, version_id = prep_file(authed=authorized)
    query = update_query
    variables = {
        "kfId": version_id,
        "description": "New description",
        "state": "PEN",
    }
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    # The operation should be successful
    if expected:
        assert resp.status_code == 200
        assert (
            resp.json()["data"]["updateVersion"]["version"]["description"]
            == "New description"
        )
        version = Version.objects.get(kf_id=version_id)
        assert version.description == "New description"
    # Should not be successful
    else:
        assert resp.status_code == 200
        assert resp.json()["data"]["updateVersion"] is None
        expected_error = "Not authenticated to mutate a version."
        assert resp.json()["errors"][0]["message"] == expected_error
        version = Version.objects.get(kf_id=version_id)


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
def test_update_state(db, admin_client, prep_file, state, expected):
    """
    Test that only valid states may be set.

    :state: Value to pass as the state field
    :expected: True if expected to pass, substring of the error message if
        it's expected to fail
    """
    study_id, file_id, version_id = prep_file()
    query = update_query
    variables = {"kfId": version_id, "description": "Test", "state": state}
    resp = admin_client.post(
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
        version = Version.objects.get(kf_id=version_id)
        assert version.state == state
    # State is not known
    else:
        assert resp.status_code == 400
        assert expected in resp.json()["errors"][0]["message"]
        version = Version.objects.get(kf_id=version_id)
