import os
import pytest
import json
import boto3
from moto import mock_s3

from creator.files.models import Object, File, DownloadToken
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory


def test_download_local(admin_client, db, prep_file):
    (study1_id, file1_id, version1_id) = prep_file()
    (study2_id, file2_id, version2_id) = prep_file(file_name="data.csv")
    resp = admin_client.get(f"/download/study/{study1_id}/file/{file1_id}")
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition") == "attachment; filename=manifest.txt"
    )
    assert resp.content == b"aaa\nbbb\nccc\n"
    resp = admin_client.get(
        f"/download/study/{study2_id}/file/{file2_id}"
        f"/version/{version2_id}"
    )
    assert resp.status_code == 200
    obj = File.objects.get(kf_id=file2_id).versions.get(kf_id=version2_id)
    assert obj.size == 24
    assert resp.get("Content-Length") == str(obj.size)
    assert resp.get("Content-Type") == "application/octet-stream"
    assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"


@mock_s3
def test_download_s3(admin_client, db, prep_file):
    s3 = boto3.client("s3")
    (study_id, file_id, version_id) = prep_file()
    resp = admin_client.get(f"/download/study/{study_id}/file/{file_id}")
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition") == "attachment; filename=manifest.txt"
    )
    assert resp.content == b"aaa\nbbb\nccc\n"
    resp = admin_client.get(
        f"/download/study/{study_id}/file/{file_id}" f"/version/{version_id}"
    )
    assert resp.status_code == 200
    obj = File.objects.get(kf_id=file_id).versions.get(kf_id=version_id)
    assert obj.size == 12
    assert resp.get("Content-Length") == str(obj.size)
    assert resp.get("Content-Type") == "application/octet-stream"
    assert resp.content == b"aaa\nbbb\nccc\n"


def test_no_file(admin_client, db):
    resp = admin_client.get(f"/download/study/study_id/file/123")
    assert resp.status_code == 404


def test_file_download_url(admin_client, db, prep_file):
    (study_id, file_id, version_id) = prep_file()
    assert File.objects.count() == 1
    query = "{allFiles { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = admin_client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    file = resp.json()["data"]["allFiles"]["edges"][0]["node"]
    expect_url = f"http://testserver/download/study/{study_id}/file/{file_id}"
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert file["downloadUrl"] == expect_url
    resp = admin_client.get(file["downloadUrl"])
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition") == "attachment; filename=manifest.txt"
    )


def test_version_download_url(admin_client, db, prep_file):
    (study_id, file_id, version_id) = prep_file()
    assert Object.objects.count() == 1
    query = "{allVersions { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = admin_client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    version = resp.json()["data"]["allVersions"]["edges"][0]["node"]
    expect_url = (
        f"http://testserver/download/study/{study_id}/file/{file_id}"
        f"/version/{version_id}"
    )
    assert version["downloadUrl"] == expect_url
    resp = admin_client.get(version["downloadUrl"])
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition") == "attachment; filename=manifest.txt"
    )


def test_study_does_not_exist(admin_client, db, prep_file):
    """
    Test that a file may not be downloaded if the study_id is not correct,
    even if the file/object ids are
    """
    (study_id, file_id, version_id) = prep_file()
    assert Object.objects.count() == 1
    url = Object.objects.first().path
    # Use a different study id that the object does not belong to
    url = url.replace("/SD_", "/XX_")
    resp = admin_client.get(url)
    assert resp.content == b"No file exists for given ID and study"
    assert resp.status_code == 404


def test_download_file_name_with_spaces(admin_client, db, prep_file):
    study_id, file_id, version_id = prep_file(file_name="name with spaces.txt")
    resp1 = admin_client.get(f"/download/study/{study_id}/file/{file_id}")
    resp2 = admin_client.get(
        f"/download/study/{study_id}/file/{file_id}" f"/version/{version_id}"
    )
    assert resp1.status_code == resp2.status_code == 200
    expected_name = "attachment; filename=name%20with%20spaces.txt"
    assert resp1.get("Content-Disposition") == expected_name
    assert resp2.get("Content-Disposition") == expected_name
    assert resp1.content == resp2.content == b"aaa\nbbb\nccc\n"


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
def test_download_auth(
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
    For a given user_type attempting to download a file in an authorized study,
    we expect them to be allowed/not allowed to download that file.
    """
    api_client = {
        "admin": admin_client,
        "service": service_client,
        "user": user_client,
        None: client,
    }[user_type]
    expected_name = "attachment; filename=manifest.txt"
    study_id, file_id, version_id = prep_file(authed=authorized)
    resp = api_client.get(f"/download/study/{study_id}/file/{file_id}")

    if expected:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == expected_name
        assert resp.content == b"aaa\nbbb\nccc\n"
    else:
        assert resp.status_code == 401
        assert resp.content == b'Not authorized to download the file'
        assert resp.get("Content-Disposition") is None


def test_file_no_longer_exist(admin_client, db):
    study = StudyFactory.create_batch(1)
    file = FileFactory.create_batch(1)
    file_id = file[0].kf_id
    query = "{allFiles { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = admin_client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    file = resp.json()["data"]["allFiles"]["edges"][0]["node"]
    resp = admin_client.get(file["downloadUrl"])
    assert resp.status_code == 404


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
def test_signed_url(
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
    resp = api_client.get(f"/signed-url/study/{study_id}/file/{file_id}")

    if expected:
        assert resp.status_code == 200
        assert resp.json()["url"].startswith(f"/download/study/{study_id}/")
    else:
        assert resp.status_code == 404


def test_signed_url_study_does_not_exist(admin_client, db, prep_file):
    """
    Test that a signed url may not be generated if the study_id is not correct,
    even if the file/object ids are
    """
    (study_id, file_id, version_id) = prep_file()
    assert Object.objects.count() == 1
    url = Object.objects.first().path
    # Use a different study id that the object does not belong to
    resp = admin_client.get(f"/signed-url/study/SD_XXXXXXXX/file/{file_id}")
    assert resp.content == b"No file exists for given ID and study"
    assert resp.status_code == 404


def test_signed_download_flow(db, user_client, admin_client, prep_file):
    """
    Test the download flow of a signed url.

    Put a file in the db
    Get a signed url to access that url with the admin user
    Download the file at that url with an unauthed user
    """
    study_id, file_id, version_id = prep_file()
    obj = Object.objects.get(kf_id=version_id)
    resp = admin_client.get(f"/signed-url/study/{study_id}/file/{file_id}")
    assert resp.status_code == 200
    assert "url" in resp.json()
    assert len(resp.json()["url"].split("=")[1]) == 27
    # Check that a new token was generated
    assert DownloadToken.objects.count() == 1
    token = DownloadToken.objects.first()
    assert token.root_object == Object.objects.first()
    # Check that token is not yet claimed
    assert token.claimed is False
    assert token.is_valid(obj) is True

    expected = "attachment; filename=manifest.txt"
    resp = user_client.get(resp.json()["url"])
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == expected
    assert resp.content == b"aaa\nbbb\nccc\n"
    # Check that token is now claimed and invalid
    token.refresh_from_db()
    assert token.claimed is True
    assert token.is_valid(obj) is False


def test_signed_download_expired(
    db, settings, user_client, admin_client, prep_file
):
    """
    Test that files may not be downloaded if token is expired
    """
    # Tokens expire immediately
    settings.DOWNLOAD_TOKEN_TTL = -1
    study_id, file_id, version_id = prep_file()
    obj = Object.objects.get(kf_id=version_id)
    resp = admin_client.get(f"/signed-url/study/{study_id}/file/{file_id}")
    assert resp.status_code == 200
    token = DownloadToken.objects.first()
    # Check that token is expired
    assert token.expired is True
    # Check that token is invalid
    assert token.is_valid(obj) is False

    resp = user_client.get(resp.json()["url"])
    assert resp.status_code == 401
