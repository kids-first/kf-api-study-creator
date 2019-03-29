import pytest
from creator.files.models import File, Object, DownloadToken, DevDownloadToken


update_query = """
mutation (
    $kfId:String!,
    $description: String!,
    $name: String!,
    $fileType: FileFileType!
) {
    updateFile(
        kfId: $kfId,
        name: $name,
        description:$description,
        fileType: $fileType
    ) {
        file { id kfId description name fileType }
    }
}
"""


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


def test_unauthed_file_mutation_query(client, db, prep_file):
    """
    File mutations are not allowed without authentication
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not authenticated to mutate a file."
    assert resp.json()["errors"][0]["message"] == expected_error


def test_my_file_mutation_query(user_client, db, prep_file):
    """
    File mutations are allowed on the files under the studies that
    the user belongs to
    """
    (_, file_id, _) = prep_file(authed=True)
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = user_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"


def test_not_my_file_mutation_query(user_client, db, prep_file):
    """
    File mutations are not allowed on the files under the studies that
    the user does not belong to
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = user_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["updateFile"] is None
    expected_error = "Not authenticated to mutate a file."
    assert resp.json()["errors"][0]["message"] == expected_error


def test_admin_file_mutation_query(admin_client, db, prep_file):
    """
    File mutations are allowed on any files for admin user
    """
    (_, file_id, _) = prep_file()
    query = update_query
    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200
    resp_file = resp.json()["data"]["updateFile"]["file"]
    assert resp_file["name"] == "New name"
    assert resp_file["description"] == "New description"


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
        assert Object.objects.count() == 0
        assert File.objects.count() == 0
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
        assert Object.objects.count() == 1
        assert File.objects.count() == 1


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
    mutation ($token: String!) {
        deleteDevToken(token: $token) {
            success
        }
    }
    """
    variables = {"token": token.token}
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
