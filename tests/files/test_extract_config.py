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


