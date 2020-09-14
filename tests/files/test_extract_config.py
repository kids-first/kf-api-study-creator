import os
import pytest
import json
import boto3
from moto import mock_s3
from django.http.response import HttpResponse

from creator.files.models import Version, File
from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory


@pytest.mark.parametrize(
    "file_type,has_config",
    [
        ("OTH", False),
        ("SEQ", False),
        ("SHM", False),
        ("CLN", False),
        ("DBG", False),
        ("FAM", False),
        ("S3S", True),
    ],
)
def test_valid_file_type(clients, db, mocker, file_type, has_config):
    client = clients.get("Administrators")
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(
        open("tests/data/s3_scrape_config_file.py")
    )
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    file.file_type = file_type
    file.save()
    version = file.versions.latest("created_at")
    resp = client.get(f"/extract_config/study/{study.kf_id}/file/{file.kf_id}")
    if has_config:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == (
            f"attachment; filename*=UTF-8''" f"{version.kf_id}_config.py"
        )
        assert b"/download/study/" in resp.content
    else:
        assert resp.status_code == 404


def test_file_not_exist(clients, db):
    client = clients.get("Administrators")
    resp = client.get(f"/extract_config/study/study_id/file/123")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_config_auth(db, mocker, clients, user_group, allowed):
    """
    For a given user_type attempting to extract config for a file in an
    authorized study, we expect them to be allowed/not allowed to download
    the config file.
    """
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)
    file.file_type = 'S3S'
    file.save()
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")
    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    expected_name = f"attachment; filename*=UTF-8''{version.kf_id}_config.py"
    resp = client.get(f"/extract_config/study/{study.kf_id}/file/{file.kf_id}")

    if allowed:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == expected_name
        assert b"/download/study/" in resp.content
    else:
        assert resp.status_code == 401
        assert resp.content == b"Not authorized to extract config for the file"
        assert resp.get("Content-Disposition") is None
