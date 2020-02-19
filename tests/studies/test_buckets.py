import json
import boto3
import pytest
from moto import mock_s3
from botocore.exceptions import ClientError
from creator.studies.factories import StudyFactory
from creator.studies.buckets import (
    new_bucket,
    get_bucket_name,
    _add_replication,
    _add_logging,
    _add_cors,
    _add_policy,
    _add_inventory,
)


@pytest.yield_fixture
def logging_bucket(settings):
    settings.STUDY_BUCKETS_LOGGING_BUCKET = "logging"
    settings.STUDY_BUCKETS_DR_LOGGING_BUCKET = "dr-logging"

    @mock_s3
    def f():
        s3 = boto3.client("s3")
        try:
            bucket = s3.create_bucket(
                ACL="log-delivery-write",
                Bucket=settings.STUDY_BUCKETS_LOGGING_BUCKET,
            )
        except ClientError as e:
            pass

        try:
            dr_bucket = s3.create_bucket(
                ACL="log-delivery-write",
                Bucket=settings.STUDY_BUCKETS_DR_LOGGING_BUCKET,
                CreateBucketConfiguration={
                    "LocationConstraint": settings.STUDY_BUCKETS_DR_REGION
                },
            )
        except ClientError as e:
            pass

    yield f


@mock_s3
def test_replication(settings, logging_bucket):
    """
    Test that adding replication to a bucket configures a dr bucket correctly
    """
    settings.STUDY_BUCKETS_REPLICATION_ROLE = (
        "arn:aws:iam::000000000000:role/study-replication-role"
    )
    logging_bucket()
    study_id = "sd-00000000"
    bucket_name = get_bucket_name(study_id)

    client = boto3.client("s3")
    bucket = client.create_bucket(ACL="private", Bucket=bucket_name)

    _add_replication(bucket_name, study_id)

    dr_bucket_name = get_bucket_name(
        "sd-00000000", region=settings.STUDY_BUCKETS_DR_REGION, suffix="dr"
    )
    bucket = boto3.resource("s3").Bucket(dr_bucket_name)

    assert len(bucket.Tagging().tag_set) == 8
    assert bucket.Versioning().status == "Enabled"

    logging = bucket.Logging().logging_enabled
    assert logging["TargetBucket"] == "dr-logging"
    assert logging["TargetPrefix"] == "studies/dev/sd-00000000-dr/"


@mock_s3
def test_replication_bucket_exists(settings, logging_bucket, mocker):
    """
    Test when dr bucket already exists
    """
    settings.STUDY_BUCKETS_REPLICATION_ROLE = (
        "arn:aws:iam::000000000000:role/study-replication-role"
    )
    logging_bucket()
    study_id = "sd-00000000"
    bucket_name = get_bucket_name(study_id)
    dr_bucket_name = get_bucket_name(
        "sd-00000000", region=settings.STUDY_BUCKETS_DR_REGION, suffix="dr"
    )

    client = boto3.client("s3")
    bucket = client.create_bucket(ACL="private", Bucket=bucket_name)
    bucket = client.create_bucket(
        ACL="private",
        Bucket=dr_bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
    )

    mock_encryption = mocker.patch("creator.studies.buckets._add_encryption")

    _add_replication(bucket_name, study_id)

    assert mock_encryption.call_count == 1

    dr_bucket = boto3.resource("s3").Bucket(dr_bucket_name)

    assert len(dr_bucket.Tagging().tag_set) == 8
    assert dr_bucket.Versioning().status == "Enabled"

    logging = dr_bucket.Logging().logging_enabled
    assert logging["TargetBucket"] == "dr-logging"
    assert logging["TargetPrefix"] == "studies/dev/sd-00000000-dr/"


@mock_s3
def test_cors(logging_bucket):
    """
    Test that buckets created have CORS for cavatica
    """
    logging_bucket()
    bucket_name = "sd-00000000"

    client = boto3.client("s3")
    s3 = boto3.resource("s3")
    client.create_bucket(ACL="private", Bucket=bucket_name)
    _add_cors(bucket_name)

    rules = s3.BucketCors(bucket_name).cors_rules
    assert len(rules) == 1
    assert rules[0]["AllowedOrigins"] == ["https://cavatica.sbgenomics.com"]


@mock_s3
def test_inventory(logging_bucket, settings):
    """
    Test that buckets created have inventory configured
    """
    settings.STUDY_BUCKETS_INVENTORY_LOCATION = "bucket-metrics/inventory"
    logging_bucket()
    bucket_name = "sd-00000000"

    import time

    client = boto3.client("s3")
    client.create_bucket(ACL="private", Bucket=bucket_name)
    r = _add_inventory(bucket_name)


@mock_s3
def test_no_delete_policy(settings, logging_bucket):
    """
    Test that buckets created have Delete* actions denied
    """
    settings.STUDY_BUCKETS_REPLICATION_ROLE = (
        "arn:aws:iam::000000000000:role/study-replication-role"
    )
    logging_bucket()
    study_id = "sd-00000000"
    bucket_name = get_bucket_name(study_id)

    def policy_check(policy, bucket):
        assert policy["Statement"][0]["Sid"] == "DenyDeleteObject"
        assert policy["Statement"][0]["Resource"] == f"arn:aws:s3:::{bucket}/*"
        assert policy["Statement"][1]["Sid"] == "DenyDeleteBucket"
        assert policy["Statement"][1]["Resource"] == f"arn:aws:s3:::{bucket}"

    client = boto3.client("s3")
    s3 = boto3.resource("s3")
    client.create_bucket(ACL="private", Bucket=bucket_name)
    _add_policy(bucket_name)
    policy = json.loads(s3.BucketPolicy(bucket_name).policy)
    policy_check(policy, bucket_name)

    # Adding replication will make a replicated bucket that should also have
    # the policy on it
    resp = _add_replication(bucket_name, study_id)
    dr_bucket_name = get_bucket_name(
        study_id, region=settings.STUDY_BUCKETS_DR_REGION, suffix="dr"
    )

    policy = json.loads(s3.BucketPolicy(dr_bucket_name).policy)
    policy_check(policy, dr_bucket_name)


@mock_s3
def test_logging(settings, logging_bucket):
    """
    Test that logging gets set up correctly
    """
    settings.STUDY_BUCKETS_LOGGING_BUCKET = "logging-bucket"
    logging_bucket()

    study_id = "sd-00000000"
    bucket_name = get_bucket_name(study_id)

    client = boto3.client("s3")
    client.create_bucket(ACL="private", Bucket=bucket_name)
    s3 = boto3.resource("s3")

    _add_logging(bucket_name, study_id)

    logging = s3.BucketLogging(bucket_name)
    assert logging.logging_enabled["TargetBucket"] == "logging-bucket"


@mock_s3
def test_logging_no_bucket(settings, logging_bucket):
    """
    Test that failing to setup logging does not kill the process
    """
    study_id = "sd-00000000"
    bucket_name = get_bucket_name(study_id)

    client = boto3.client("s3")
    client.create_bucket(ACL="private", Bucket=bucket_name)
    s3 = boto3.resource("s3")

    _add_logging(bucket_name, study_id)

    logging = s3.BucketLogging(bucket_name)
    assert logging.logging_enabled is None


@mock_s3
def test_new_bucket(db, mocker):
    study = StudyFactory()
    mock_encryption = mocker.patch("creator.studies.buckets._add_encryption")
    mock_tagging = mocker.patch("creator.studies.buckets._add_tagging")
    mock_versioning = mocker.patch("creator.studies.buckets._add_versioning")
    mock_logging = mocker.patch("creator.studies.buckets._add_logging")
    mock_cors = mocker.patch("creator.studies.buckets._add_cors")
    mock_replication = mocker.patch("creator.studies.buckets._add_replication")
    mock_inventory = mocker.patch("creator.studies.buckets._add_inventory")

    new_bucket(study)

    assert mock_encryption.call_count == 1
    assert mock_tagging.call_count == 1
    assert mock_versioning.call_count == 1
    assert mock_logging.call_count == 1
    assert mock_cors.call_count == 1
    assert mock_replication.call_count == 1
    assert mock_inventory.call_count == 1
