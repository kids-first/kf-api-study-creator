import pytest
from creator.files.models import Object, DownloadToken


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
    api_client = {"admin": admin_client, "user": user_client, None: client}[
        user_type
    ]
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
        download = client.get(resp_body['url'])
        assert download.status_code == 200
        assert download.content == b'aaa\nbbb\nccc\n'
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
