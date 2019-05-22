import pytest
from creator.files.models import File, Version


@pytest.mark.parametrize(
    "user_type,authorized,expected",
    [
        ("admin", True, True),
        ("admin", False, True),
        ("service", True, True),
        ("service", False, True),
        ("user", True, False),
        ("user", False, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_delete_file_mutation(
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
    Test that a file may be deleted through the deleteFile mutation.
    Only admin users may delete a file
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    study_id, file_id, version_id = prep_file(authed=authorized)
    query = """
    mutation ($kfId: String!) {
        deleteFile(kfId: $kfId) {
            success
        }
    }
    """
    variables = {"kfId": file_id}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["deleteFile"]
        assert resp.status_code == 200
        assert resp_body["success"] is True
        assert Version.objects.count() == 0
        assert File.objects.count() == 0
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Version.objects.count() == 1
        assert File.objects.count() == 1
