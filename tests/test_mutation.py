import pytest
from creator.files.models import File, Object, DownloadToken, DevDownloadToken


@pytest.mark.parametrize(
    "user_type,expected",
    [("admin", True), ("service", True), ("user", False), (None, False)],
)
def test_create_dev_download_token_mutation(
    db,
    admin_client,
    service_client,
    user_client,
    client,
    prep_file,
    user_type,
    expected,
):
    """
    Test that a dev download token may created by an admin.
    Only admins may create dev download tokens
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    study_id, file_id, version_id = prep_file()
    query = """
    mutation ($name: String!) {
        createDevToken(name: $name) {
            token {
                id
                name
                token
                createdAt
            }
        }
    }
    """
    variables = {"name": "test token"}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if expected:
        assert resp.status_code == 200
        resp_body = resp.json()["data"]["createDevToken"]
        assert "token" in resp_body
        token = resp_body["token"]
        assert "name" in token
        assert "token" in token
        assert "createdAt" in token
        url = File.objects.first().path
        resp = client.get(f'{url}?token={token["token"]}')
        assert resp.status_code == 200
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Object.objects.count() == 1
        assert File.objects.count() == 1


def test_dev_token_unique_name(db, admin_client):
    """
    Test that dev tokens may not be created with the same name
    """
    query = """
    mutation ($name: String!) {
        createDevToken(name: $name) {
            token {
                id
                name
                token
                createdAt
            }
        }
    }
    """
    variables = {"name": "test token"}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    resp_body = resp.json()["data"]["createDevToken"]
    assert "token" in resp_body
    token = resp_body["token"]
    assert "name" in token
    assert "token" in token
    assert "createdAt" in token

    # Try to make another token with the same name
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_body = resp.json()
    assert "errors" in resp_body
    assert resp_body["errors"][0]["message"].endswith("already exists.")


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
def test_delete_dev_token_mutation(
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
    Test that a dev token  may be deleted through the deleteDevToken mutation.
    Only admin users may delete a token
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    token = DevDownloadToken(name="test token")
    token.save()
    query = """
    mutation ($name: String!) {
        deleteDevToken(name: $name) {
            success
        }
    }
    """
    variables = {"name": token.name}
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    assert resp.status_code == 200
    if expected:
        resp_body = resp.json()["data"]["deleteDevToken"]
        assert resp_body["success"] is True
        assert DevDownloadToken.objects.count() == 0
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert DevDownloadToken.objects.count() == 1
