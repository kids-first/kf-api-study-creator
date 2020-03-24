import pytest
from creator.files.models import Version, DownloadToken
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory


def test_signed_url_mutation_file_id_only(db, clients, versions):
    """
    Test that a signed url may be obtained using the signedUrl mutation
    given only a study_id and file_id
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = """
    mutation ($studyId: String!, $fileId: String!) {
        signedUrl(studyId: $studyId, fileId: $fileId) {
            url
        }
    }
    """
    variables = {"studyId": study.kf_id, "fileId": file.kf_id}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200

    resp_url = resp.json()["data"]["signedUrl"]["url"]
    obj = Version.objects.get(kf_id=version.kf_id)
    token = DownloadToken.objects.first()
    # Token should not be claimed yet
    assert token.claimed is False
    assert resp_url == f"{obj.path}?token={token.token}"
    # Now try to download the signed url
    resp = client.get(resp_url)
    assert resp.status_code == 200
    token.refresh_from_db()
    assert token.claimed is True


def test_signed_url_mutation(db, clients, versions):
    """
    Test that a signed url may be obtained using the signedUrl mutation
    given a study_id, file_id, and version_id
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study.kf_id,
        "fileId": file.kf_id,
        "versionId": version.kf_id,
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert resp.status_code == 200

    resp_url = resp.json()["data"]["signedUrl"]["url"]
    obj = Version.objects.get(kf_id=version.kf_id)
    token = DownloadToken.objects.first()
    # Token should not be claimed yet
    assert token.claimed is False
    assert resp_url == f"{obj.path}?token={token.token}"
    # Now try to download the signed url
    resp = client.get(resp_url)
    assert resp.status_code == 200
    token.refresh_from_db()
    assert token.claimed is True


def test_signed_url_file_not_exists(db, clients, versions):
    """
    Test that we may not retrieve a url for a file that does not exist
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study.kf_id,
        "fileId": "blah",
        "versionId": version.kf_id,
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("No file exists")


def test_signed_url_version_not_exists(db, clients, versions):
    """
    Test that we may not retrieve a url for a version that does not exist
    """
    client = clients.get("Administrators")
    study, file, version = versions

    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study.kf_id,
        "fileId": file.kf_id,
        "versionId": "blah",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"].startswith("No version exists")


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_signed_url_mutation(db, clients, versions, user_group, allowed):
    """
    Verify that a signed url may only be issued for files which the user is
    allowed to access.
    Admins can access all files, users may only access files in studies which
    they belong to, and unauthed users may not generate download urls.
    """
    client = clients.get(user_group)
    study, file, version = versions

    query = """
    mutation ($studyId: String!, $fileId: String!, $versionId: String) {
        signedUrl(studyId: $studyId, fileId: $fileId, versionId: $versionId) {
            url
        }
    }
    """
    variables = {
        "studyId": study.kf_id,
        "fileId": file.kf_id,
        "versionId": version.kf_id,
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": query, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["signedUrl"]
        assert resp.status_code == 200
        assert resp_body["url"].startswith(f"/download/study/{study.kf_id}/")
        assert "?token" in resp_body["url"]
        download = client.get(resp_body["url"])
        assert download.status_code == 200
        assert download.content == b"aaa\nbbb\nccc\n"
    else:
        assert resp.status_code == 200
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"].startswith("Not auth")
