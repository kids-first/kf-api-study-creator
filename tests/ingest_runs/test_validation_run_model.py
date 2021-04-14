import os
import pytest
import boto3
from moto import mock_s3

from django_s3_storage.storage import S3Storage
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

from creator.ingest_runs.models import (
    ValidationRun,
    ValidationResultset,
)
from creator.data_reviews.factories import DataReview, DataReviewFactory

User = get_user_model()


def test_validation_run(db, data_review):
    """
    Test ValidationRun model
    """
    # Create a good validation run for the review
    vr = ValidationRun(data_review=data_review)
    vr.clean()
    vr.save()
    # Check that study, versions, and input_hash got set right
    versions = [v.pk for v in vr.versions.all()]
    assert set(versions) == set([v.pk for v in data_review.versions.all()])
    assert vr.input_hash
    assert vr.study == data_review.study


def test_validation_resultset(db, data_review):
    """
    Test ValidationResultset model
    """
    vr = data_review.validation_resultset
    vr.clean()
    assert vr.study == data_review.study
    assert vr.data_review.pk in vr.report_path
    assert vr.data_review.pk in vr.results_path


def test_missing_study(db):
    """
    Test missing study on ValidationRun and ValidationResultset
    """
    # No data review no study
    objs = [ValidationRun(), ValidationResultset()]
    for obj in objs:
        with pytest.raises(ValidationError) as e:
            obj.clean()
            assert "must have an associated DataReview" in str(e)

    # Has data review with no study
    for obj in objs:
        obj.data_review = DataReview()
        with pytest.raises(ValidationError) as e:
            obj.clean()
            assert "must have an associated DataReview" in str(e)


@pytest.mark.parametrize(
    "file_field",
    ["report_file", "results_file"]
)
def test_file_upload_local(
    db, clients, tmp_uploads_local, file_field, data_review
):
    """
    Test validation report/results file uploads
    """
    vrs = data_review.validation_resultset
    file_field = getattr(vrs, file_field)
    file_field.save(f"foo.ext", ContentFile("foo"))
    assert vrs.study.bucket in file_field.path
    assert settings.UPLOAD_DIR in file_field.path
    assert os.path.exists(file_field.path)


@pytest.mark.parametrize(
    "file_field",
    ["report_file", "results_file"]
)
@mock_s3
def test_file_upload_s3(
    db, clients, tmp_uploads_s3, file_field, data_review
):
    """
    Test validation report/results file uploads
    """
    s3 = boto3.client("s3")
    vrs = data_review.validation_resultset
    bucket = tmp_uploads_s3(bucket_name=data_review.study.bucket)

    file_field = getattr(vrs, file_field)
    file_field.storage = S3Storage(
        aws_s3_bucket_name=data_review.study.bucket
    )
    file_field.save(f"foo.ext", ContentFile("foo"))
    assert vrs.study.bucket in file_field.url
    assert settings.UPLOAD_DIR in file_field.url
    objs = s3.list_objects(Bucket=vrs.study.bucket)["Contents"]
    assert len(objs) == 1
    assert vrs.study.bucket in objs[0]["Key"]
    assert f"foo.ext" in objs[0]["Key"]
