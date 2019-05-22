import pytest
from creator.files.models import Version


update_query = """
mutation (
    $kfId:String!,
    $description: String!
) {
    updateVersion(
        kfId: $kfId,
        description:$description
    ) {
        version { id kfId description size }
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
    variables = {"kfId": version_id, "description": "New description"}
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
