import os
import pytest
from moto import mock_s3

import boto3
from graphql_relay import to_global_id
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.core.files import File
from django_s3_storage.storage import S3Storage

from creator.studies.models import Membership
from creator.data_reviews.factories import DataReviewFactory
from creator.ingest_runs.factories import ValidationResultsetFactory

User = get_user_model()


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
def test_local_download_and_delete(
    clients, db, mocker, data_review, user_group, allowed,
):
    """
    Test download of validation report and results files
    Test download after local file is deleted
    """
    mock_resp = mocker.patch("creator.ingest_runs.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    # Upload file and save validation resultset
    file_field = data_review.validation_resultset.report_file
    file_field.save("data.csv", File(open("tests/data/data.csv")))

    # Download file
    client = clients.get(user_group)
    download_url = data_review.validation_resultset.report_path
    resp = client.get(download_url)

    if allowed:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == (
            f"attachment; filename*=UTF-8''"
            f"{file_field.name.split('/')[-1]}"
        )
        assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"
        assert resp.get("Content-Length") == str(
            os.stat("tests/data/data.csv").st_size
        )
        # Delete file from storage system
        file_field.storage.delete(file_field.name)

        # Try to download
        resp = client.get(download_url)
        assert resp.status_code == 404
        assert b"file does not exist" in resp.content
    else:
        resp.status_code == 401


@mock_s3
def test_s3_download_and_delete(
    clients, db, mocker, tmp_uploads_s3, settings, data_review
):
    """
    Test s3 download of validation report and results files
    Test download after s3 file is deleted
    """
    mock_resp = mocker.patch("creator.ingest_runs.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    # Upload file
    settings.DEFAULT_FILE_STORAGE = "django_s3_storage.storage.S3Storage"
    file_field = data_review.validation_resultset.report_file
    tmp_uploads_s3(bucket_name=data_review.study.bucket)
    file_field.storage = S3Storage(
        aws_s3_bucket_name=data_review.study.bucket
    )
    file_field.save("data.csv", File(open("tests/data/data.csv")))
    assert file_field.storage.exists(file_field.name)

    # Download file
    client = clients.get("Administrators")
    download_url = data_review.validation_resultset.report_path
    resp = client.get(download_url)

    resp.status_code == 200
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''"
        f"{file_field.name.split('/')[-1]}"
    )
    assert resp.content == b"aaa,bbb,ccc\nddd,eee,fff\n"
    assert resp.get("Content-Length") == str(
        os.stat("tests/data/data.csv").st_size
    )
    # Delete file from storage system
    file_field.storage.delete(file_field.name)

    # Try to download
    resp = client.get(download_url)
    assert resp.status_code == 404
    assert b"file does not exist" in resp.content


def test_no_validation_result(clients, db, data_review):
    """
    Test download failures

    Data review not found
    Data review validation results don't exist
    """
    client = clients.get("Administrators")

    # Data review not found
    resp = client.get("/download/data_review/foo/validation/report")
    assert resp.status_code == 404
    assert b"No data review exists" in resp.content

    # Data review validation result set doesn't exist yet
    dr = DataReviewFactory()
    download_urls = [
        f"/download/data_review/{dr.kf_id}/validation/{ft}"
        for ft in ["report", "results"]
    ]
    for url in download_urls:
        resp = client.get(url)
        assert resp.status_code == 404
        assert b"Validation results not yet available" in resp.content


def test_file_not_found(clients, db, mocker, tmpdir, data_review):
    """
    Test validation report/results files have not been uploaded
    """
    client = clients.get("Administrators")

    for ft in ["report", "results"]:
        # Validation result set has no file uploaded yet
        download_url = (
            f"/download/data_review/{data_review.kf_id}/validation/{ft}"
        )
        resp = client.get(download_url)
        assert resp.status_code == 404
        assert b"file does not exist" in resp.content
