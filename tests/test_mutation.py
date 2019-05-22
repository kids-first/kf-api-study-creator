import pytest
from creator.files.models import File, Object, DownloadToken, DevDownloadToken


def test_signed_url_mutation_file_id_only(db, admin_client, client, prep_file):
    """
    Test that a signed url may be obtained using the signedUrl mutation
    given only a study_id and file_id
    """
    study_id, file_id, version_id = prep_file()
    query = """
    mutation ($studyId: String!, $fileId: String!) {
        signedUrl(studyId: $studyId, fileId: $fileId) {
            url
        }
    }
    """
    variables = {"studyId": study_id, "fileId": file_id}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200

    resp_url = resp.json()["data"]["signedUrl"]["url"]
    obj = Object.objects.get(kf_id=version_id)
    token = DownloadToken.objects.first()
    # Token should not be claimed yet
    assert token.claimed is False
    assert resp_url == f"{obj.path}?token={token.token}"
    # Now try to download the signed url
    resp = client.get(resp_url)
    assert resp.status_code == 200
    token.refresh_from_db()
    assert token.claimed is True


def test_signed_url_mutation(db, admin_client, client, prep_file):
    """
    Test that a signed url may be obtained using the signedUrl mutation
    given a study_id, file_id, and version_id
    """
    study_id, file_id, version_id = prep_file()
    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study_id,
        "fileId": file_id,
        "versionId": version_id,
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200

    resp_url = resp.json()["data"]["signedUrl"]["url"]
    obj = Object.objects.get(kf_id=version_id)
    token = DownloadToken.objects.first()
    # Token should not be claimed yet
    assert token.claimed is False
    assert resp_url == f"{obj.path}?token={token.token}"
    # Now try to download the signed url
    resp = client.get(resp_url)
    assert resp.status_code == 200
    token.refresh_from_db()
    assert token.claimed is True


def test_signed_url_file_not_exists(db, admin_client, prep_file):
    """
    Test that we may not retrieve a url for a file that does not exist
    """
    study_id, file_id, version_id = prep_file()
    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study_id,
        "fileId": "blah",
        "versionId": version_id,
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("No file exists")


def test_signed_url_version_not_exists(db, admin_client, prep_file):
    """
    Test that we may not retrieve a url for a version that does not exist
    """
    study_id, file_id, version_id = prep_file()
    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {"studyId": study_id, "fileId": file_id, "versionId": "blah"}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("No version exists")


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
def test_signed_url_mutation(
    db,
    admin_client,
    user_client,
    service_client,
    client,
    prep_file,
    user_type,
    authorized,
    expected,
):
    """
    Verify that a signed url may only be issued for files which the user is
    allowed to access.
    Admins can access all files, users may only access files in studies which
    they belong to, and unauthed users may not generate download urls.
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    study_id, file_id, version_id = prep_file(authed=authorized)
    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study_id,
        "fileId": file_id,
        "versionId": version_id,
    }
    resp = api_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if expected:
        resp_body = resp.json()["data"]["signedUrl"]
        assert resp.status_code == 200
        assert resp_body["url"].startswith(f"/download/study/{study_id}/")
        assert "?token" in resp_body["url"]
        download = client.get(resp_body["url"])
        assert download.status_code == 200
        assert download.content == b"aaa\nbbb\nccc\n"
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")


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
