import boto3
import pytest
from moto import mock_s3
from creator.studies.factories import StudyFactory
from creator.buckets.models import Bucket
from creator.buckets.scanner import sync_buckets


@mock_s3
def test_sync_buckets(db):
    """
    Test that bucket syncing only pulls study buckets
    """
    client = boto3.client("s3")
    bucket1 = client.create_bucket(Bucket="not-a-study")
    bucket2 = client.create_bucket(Bucket="kf-dev-sd-00000000")

    assert Bucket.objects.count() == 0

    sync_buckets()
    assert Bucket.objects.count() == 1
    assert Bucket.objects.first().name == "kf-dev-sd-00000000"


@mock_s3
def test_sync_buckets_idempotency(db):
    """
    Test that running twice results in the same state
    """
    client = boto3.client("s3")
    bucket = client.create_bucket(Bucket="kf-dev-sd-00000000")

    assert Bucket.objects.count() == 0

    sync_buckets()
    assert Bucket.objects.count() == 1

    sync_buckets()
    assert Bucket.objects.count() == 1


@mock_s3
def test_sync_buckets_bad_response(mocker):
    """
    Test that problems listing buckets are handled gracefully
    """

    mock = mocker.patch("creator.buckets.scanner.boto3")
    mock.client().list_buckets.side_effect = Exception("Access error")

    with pytest.raises(Exception) as exc:
        sync_buckets()


@mock_s3
def test_sync_buckets_deleted(db):
    """
    Test that deleted buckets get marked correctly
    """
    client = boto3.client("s3")
    bucket = client.create_bucket(Bucket="kf-dev-sd-00000000")

    assert Bucket.objects.count() == 0

    sync_buckets()
    assert not Bucket.objects.first().deleted
    client.delete_bucket(Bucket="kf-dev-sd-00000000")

    sync_buckets()
    assert Bucket.objects.first().deleted


@mock_s3
def test_sync_buckets_study_linked(db):
    """
    Test that the study bucket is correctly linked to a study
    """
    study = StudyFactory(kf_id="SD_00000000")
    client = boto3.client("s3")
    bucket1 = client.create_bucket(Bucket="not-a-study")
    bucket1 = client.create_bucket(Bucket="kf-dev-sd-00000000")
    bucket2 = client.create_bucket(Bucket="kf-dev-sd-00000001")

    sync_buckets()
    assert (
        Bucket.objects.filter(name="kf-dev-sd-00000000").first().study == study
    )
    assert Bucket.objects.count() == 2


@mock_s3
def test_sync_buckets_study_does_not_exist(db):
    """
    Test that a bucket is not linked if a corresponding study does not exist
    """
    client = boto3.client("s3")
    bucket1 = client.create_bucket(Bucket="kf-dev-sd-00000000")
    bucket2 = client.create_bucket(Bucket="kf-dev-sd-00000001")

    sync_buckets()
    assert (
        Bucket.objects.filter(name="kf-dev-sd-00000000").first().study is None
    )
    assert Bucket.objects.count() == 2
