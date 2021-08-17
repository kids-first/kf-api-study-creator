import os
import pytest
import json
import boto3
from moto import mock_s3
from django.core import management
from django.http.response import HttpResponse

from creator.files.models import Version, File, DownloadToken
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory


def test_download_local(clients, db, mocker):
    client = clients.get("Administrators")
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))
    study1 = StudyFactory()
    study2 = StudyFactory()
    file1 = FileFactory(study=study1)
    file2 = FileFactory(study=study2)
    version1 = file1.versions.latest("created_at")
    version2 = file2.versions.latest("created_at")
    resp = client.get(f"/download/study/{study1.kf_id}/file/{file1.kf_id}")
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''"
        f"{version1.kf_id}_{version1.file_name}"
    )
    assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"
    resp = client.get(
        f"/download/study/{study2.kf_id}/file/{file2.kf_id}"
        f"/version/{version2.kf_id}"
    )
    assert resp.status_code == 200
    obj = File.objects.get(kf_id=file2.kf_id).versions.get(
        kf_id=version2.kf_id
    )
    assert resp.get("Content-Length") == str(obj.size)
    assert resp.get("Content-Type") == "application/octet-stream"
    assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"


def test_no_file(clients, db):
    client = clients.get("Administrators")
    resp = client.get(f"/download/study/study_id/file/123")
    assert resp.status_code == 404


def test_file_download_url(clients, db, mocker):
    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")

    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    assert File.objects.count() == 1

    query = "{allFiles { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    file_json = resp.json()["data"]["allFiles"]["edges"][0]["node"]
    expect_url = (
        f"https://testserver/download/study/{study.kf_id}/file/{file.kf_id}"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allFiles" in resp.json()["data"]
    assert file_json["downloadUrl"] == expect_url
    resp = client.get(file_json["downloadUrl"])
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition")
        == f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )


def test_file_download_url_develop(clients, db, mocker, settings):
    settings.DEVELOP = True
    management.call_command("setup_test_user")
    client = clients.get("Administrators")

    study = StudyFactory(files=0)
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")

    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    assert File.objects.count() == 1

    query = "{allFiles { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    file_json = resp.json()["data"]["allFiles"]["edges"][0]["node"]
    expect_url = (
        f"http://testserver/download/study/{study.kf_id}/file/{file.kf_id}"
    )
    assert file_json["downloadUrl"] == expect_url


def test_version_download_url(db, clients, mocker):
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")

    query = """
    {
        allVersions(orderBy: "-created_at") {
            edges { node { downloadUrl } }
        }
    }
    """
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    version_json = resp.json()["data"]["allVersions"]["edges"][0]["node"]
    expect_url = (
        f"https://testserver/download/study/{study.kf_id}/file/{file.kf_id}"
        f"/version/{version.kf_id}"
    )
    assert version_json["downloadUrl"] == expect_url
    resp = client.get(version_json["downloadUrl"])
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition")
        == f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )


def test_version_download_url_develop(db, clients, mocker, settings):
    settings.DEVELOP = True
    management.call_command("setup_test_user")
    client = clients.get("Administrators")
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    study = StudyFactory(files=0)
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")

    query = """
    {
        allVersions(orderBy: "-created_at") {
            edges { node { downloadUrl } }
        }
    }
    """
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    version_json = resp.json()["data"]["allVersions"]["edges"][0]["node"]
    expect_url = (
        f"http://testserver/download/study/{study.kf_id}/file/{file.kf_id}"
        f"/version/{version.kf_id}"
    )
    assert version_json["downloadUrl"] == expect_url
    resp = client.get(version_json["downloadUrl"])
    assert resp.status_code == 200
    assert (
        resp.get("Content-Disposition")
        == f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )


def test_study_does_not_exist(db, mocker, clients):
    """
    Test that a file may not be downloaded if the study_id is not correct,
    even if the file/object ids are
    """
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")

    url = version.path
    # Use a different study id that the object does not belong to
    url = url.replace("/SD_", "/XX_")
    resp = client.get(url)
    assert resp.content == b"No file exists for given ID and study"
    assert resp.status_code == 404


def test_download_file_name_with_spaces(db, clients, mocker, upload_file):
    client = clients.get("Administrators")
    study = StudyFactory()

    file_name = "name with spaces.txt"
    upload = upload_file(study.kf_id, file_name, client)
    file_id = upload.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    version = file.versions.latest("created_at")
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open(f"tests/data/{file_name}"))

    resp1 = client.get(f"/download/study/{study.kf_id}/file/{file.kf_id}")
    resp2 = client.get(
        f"/download/study/{study.kf_id}/file/{file.kf_id}"
        f"/version/{version.kf_id}"
    )
    assert resp1.status_code == resp2.status_code == 200
    expected_name = (
        f"attachment; filename*=UTF-8''"
        f"{version.kf_id}_name%20with%20spaces.txt"
    )
    assert resp1.get("Content-Disposition") == expected_name
    assert resp2.get("Content-Disposition") == expected_name
    assert resp1.content == resp2.content == b"aaa\nbbb\nccc\n"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", False),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_download_auth(db, mocker, clients, user_group, allowed):
    """
    For a given user_type attempting to download a file in an authorized study,
    we expect them to be allowed/not allowed to download that file.
    """
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")
    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    expected_name = (
        f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )
    resp = client.get(f"/download/study/{study.kf_id}/file/{file.kf_id}")

    if allowed:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == expected_name
        assert resp.content == b"aaa\nbbb\nccc\n"
    else:
        assert resp.status_code == 401
        assert resp.content == b"Not authorized to download the file"
        assert resp.get("Content-Disposition") is None


def test_file_no_longer_exist(db, clients):
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    query = "{allFiles { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    file = resp.json()["data"]["allFiles"]["edges"][0]["node"]
    resp = client.get(file["downloadUrl"])
    assert resp.status_code == 404


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
def test_signed_url(db, clients, user_group, allowed):
    """
    Verify that a signed url may only be issued for files which the user is
    allowed to access.
    Admins can access all files, users may only access files in studies which
    they belong to, and unauthed users may not generate download urls.
    """
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)

    resp = client.get(f"/signed-url/study/{study.kf_id}/file/{file.kf_id}")

    if allowed:
        assert resp.status_code == 200
        assert resp.json()["url"].startswith(f"/download/study/{study.kf_id}/")
    else:
        assert resp.status_code == 404


def test_signed_url_study_does_not_exist(db, clients):
    """
    Test that a signed url may not be generated if the study_id is not correct,
    even if the file/object ids are
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    # Use a different study id that the object does not belong to
    resp = client.get(f"/signed-url/study/SD_XXXXXXXX/file/{file.kf_id}")
    assert resp.content == b"No file exists for given ID and study"
    assert resp.status_code == 404


def test_signed_download_flow(db, mocker, clients):
    """
    Test the download flow of a signed url.

    Put a file in the db
    Get a signed url to access that url with the admin user
    Download the file at that url with an unauthed user
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")

    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    resp = client.get(f"/signed-url/study/{study.kf_id}/file/{file.kf_id}")
    assert resp.status_code == 200
    assert "url" in resp.json()
    assert len(resp.json()["url"].split("=")[1]) == 27
    # Check that a new token was generated
    assert DownloadToken.objects.count() == 1
    token = DownloadToken.objects.first()
    assert token.root_version == version
    # Check that token is not yet claimed
    assert token.claimed is False
    assert token.is_valid(version) is True

    expected = (
        f"attachment; filename*=UTF-8''{version.kf_id}_{version.file_name}"
    )
    resp = client.get(resp.json()["url"])
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == expected
    assert resp.content == b"aaa\nbbb\nccc\n"
    # Check that token is now claimed and invalid
    token.refresh_from_db()
    assert token.claimed is True
    assert token.is_valid(version) is False


def test_signed_download_expired(db, settings, clients, mocker):
    """
    Test that files may not be downloaded if token is expired
    """
    client = clients.get("Developers")
    # Tokens expire immediately
    settings.DOWNLOAD_TOKEN_TTL = -1
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")

    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    resp = client.get(f"/signed-url/study/{study.kf_id}/file/{file.kf_id}")
    assert resp.status_code == 200
    token = DownloadToken.objects.first()
    # Check that token is expired
    assert token.expired is True
    # Check that token is invalid
    assert token.is_valid(version) is False

    client = clients.get(None)
    resp = client.get(resp.json()["url"])
    assert resp.status_code == 401
