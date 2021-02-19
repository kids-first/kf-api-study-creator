import json
import boto3
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


POLICY = """{{
      "Version": "2012-10-17",
      "Id": "kf001",
      "Statement": [
          {{
              "Sid": "DenyDeleteObject",
              "Effect": "Deny",
              "Principal": "*",
              "Action": [
                "s3:DeleteObjectTagging",
                "s3:DeleteObjectVersionTagging",
                "s3:DeleteObjectVersion",
                "s3:DeleteObject"
              ],
              "Resource": "arn:aws:s3:::{bucket_name}/*"
          }},
          {{
              "Sid": "DenyDeleteBucket",
              "Effect": "Deny",
              "Principal": "*",
              "Action": [
                "s3:DeleteBucket"
              ],
              "Resource": "arn:aws:s3:::{bucket_name}"
          }}
      ]
}}"""


def get_bucket_name(study_id, region=None, suffix=""):
    if region is None:
        region = settings.STUDY_BUCKETS_REGION

    name = "kf-study-{}-{}-{}".format(
        region, settings.STAGE, study_id.replace("_", "-")
    ).lower()

    if len(suffix) > 0:
        name += f"-{suffix}"

    return name


def new_bucket(study):
    """
    Create a new bucket in s3 given a study_id
    """
    study_id = study.kf_id

    s3 = boto3.client("s3")
    bucket_name = get_bucket_name(study_id)
    bucket = s3.create_bucket(ACL="private", Bucket=bucket_name)
    _add_policy(bucket_name)

    # Encryption
    logger.info("adding encryption to bucket")
    _add_encryption(bucket_name)

    # Tagging
    logger.info("adding tagging to bucket")
    _add_tagging(bucket_name, study_id)

    # Versioning
    logger.info("adding versioning to bucket")
    _add_versioning(bucket_name)

    # Logging
    logger.info("adding logging to bucket")
    _add_logging(bucket_name, study_id)

    # CORS
    logger.info("adding CORS to bucket")
    _add_cors(bucket_name)

    # Replication
    logger.info("adding replication to bucket")
    _add_replication(bucket_name, study_id)

    # Inventory
    logger.info("adding inventory to bucket")
    _add_inventory(bucket_name)

    study.bucket = bucket_name

    return study


def _add_versioning(bucket_name):
    """
    Enabled versioning for a bucket
    """
    s3 = boto3.client("s3")
    response = s3.put_bucket_versioning(
        Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"}
    )
    return response


def _add_encryption(bucket_name):
    """
    Adds encryption to a bucket
    """
    s3 = boto3.client("s3")
    response = s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        },
    )
    return response


def _add_tagging(bucket_name, study_id):
    """
    Adds standard tag set to a bucket
    """
    s3 = boto3.client("s3")
    response = s3.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={
            "TagSet": [
                {"Key": "Name", "Value": f"{study_id}"},
                {
                    "Key": "Description",
                    "Value": f"harmonized and source files for {study_id}",
                },
                {"Key": "Environment", "Value": settings.STAGE},
                {"Key": "AppId", "Value": "kf-api-bucket-service"},
                {"Key": "Owner", "Value": "d3b"},
                {"Key": "kf_id", "Value": study_id},
                {"Key": "ResourceRole", "Value": "study bucket"},
                {"Key": "Confidentiality", "Value": "Deidentified"},
            ]
        },
    )
    return response


def _add_logging(bucket_name, study_id):
    """
    Adds access logging to a bucket
    """
    s3 = boto3.client("s3")
    # Logging buckets need to be in the same region, determine based on name
    if "-dr" in bucket_name:
        target_logging_bucket = settings.STUDY_BUCKETS_DR_LOGGING_BUCKET
    else:
        target_logging_bucket = settings.STUDY_BUCKETS_LOGGING_BUCKET

    # Go to logging bucket under STAGE/STUDY_ID{-dr}/
    if bucket_name.endswith("-dr"):
        study_id += "-dr"
    log_prefix = f"studies/{settings.STAGE}/{study_id}/"
    try:
        response = s3.put_bucket_logging(
            Bucket=bucket_name,
            BucketLoggingStatus={
                "LoggingEnabled": {
                    "TargetBucket": target_logging_bucket,
                    "TargetPrefix": log_prefix,
                }
            },
        )
        return response
    except s3.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "InvalidTargetBucketForLogging":
            logger.error(
                f"logging not enabled, log bucket not found "
                + f"{target_logging_bucket}"
            )
        else:
            logger.error(err)


def _add_replication(bucket_name: str, study_id: str):
    """
    Configures a second bucket with `-dr` suffix and replicates the primary
    bucket to it.
    Adds a lifecycle policy to the dr bucket to immediately roll data into
    glacier for cold storage
    """
    if not settings.FEAT_STUDY_BUCKETS_REPLICATION_ENABLED:
        logger.info(
            "FEAT_STUDY_BUCKETS_REPLICATION_ENABLED is set to False. "
            f"Will not create replication bucket for {bucket_name}."
        )
        return
    dr_bucket_name = get_bucket_name(
        study_id, region=settings.STUDY_BUCKETS_DR_REGION, suffix="dr"
    )

    s3 = boto3.client("s3")
    logger.info(f"Creating a replication bucket at {dr_bucket_name}")
    # Set up a second -dr bucket to replicate to
    try:
        bucket = s3.create_bucket(
            ACL="private",
            Bucket=dr_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        _add_policy(dr_bucket_name)
    except s3.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            logger.info(f"bucket {dr_bucket_name} already exists, continuing")

    logger.info("adding encryption to replicated bucket")
    _add_encryption(dr_bucket_name)
    logger.info("adding versioning to replicated bucket")
    _add_versioning(dr_bucket_name)
    logger.info("adding tagging to replicated bucket")
    _add_tagging(dr_bucket_name, study_id)
    logger.info("adding logging to replicated bucket")
    _add_logging(dr_bucket_name, study_id)

    # Add the replication rule
    iam_role = settings.STUDY_BUCKETS_REPLICATION_ROLE
    response = s3.put_bucket_replication(
        Bucket=bucket_name,
        ReplicationConfiguration={
            "Role": iam_role,
            "Rules": [
                {
                    "ID": "string",
                    "Status": "Enabled",
                    "Prefix": "",
                    "Destination": {
                        "Bucket": "arn:aws:s3:::" + dr_bucket_name,
                        "StorageClass": "GLACIER",
                    },
                }
            ],
        },
    )

    return response


def _add_cors(bucket):
    """
    Adds CORS for Cavatica requests
    """
    client = boto3.client("s3")
    return client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedHeaders": [
                        "Authorization",
                        "Content-Range",
                        "Accept",
                        "Content-Type",
                        "Origin",
                        "Range",
                    ],
                    "AllowedMethods": ["GET"],
                    "AllowedOrigins": ["https://cavatica.sbgenomics.com"],
                    "ExposeHeaders": [
                        "Content-Range",
                        "Content-Length",
                        "ETag",
                    ],
                    "MaxAgeSeconds": 3000,
                }
            ]
        },
    )


def _add_policy(bucket):
    """
    Adds a policy to the bucket. Will replace whatever policy already exists,
    if there is one.
    """
    client = boto3.client("s3")
    policy = POLICY.format(bucket_name=bucket)
    return client.put_bucket_policy(Bucket=bucket, Policy=policy)


def _add_inventory(bucket):
    """
    Adds inventory configuration to a bucket
    """
    client = boto3.client("s3")
    dest = "arn:aws:s3:::{}".format(settings.STUDY_BUCKETS_INVENTORY_LOCATION)

    return client.put_bucket_inventory_configuration(
        Bucket=bucket,
        Id="StudyBucketInventory",
        InventoryConfiguration={
            "Destination": {
                "S3BucketDestination": {
                    "Bucket": dest,
                    "Format": "CSV",
                    "Prefix": "inventories",
                    "Encryption": {"SSES3": {}},
                }
            },
            "IsEnabled": True,
            "Id": "StudyBucketInventory",
            "IncludedObjectVersions": "All",
            "OptionalFields": [
                "Size",
                "LastModifiedDate",
                "StorageClass",
                "ETag",
                "IsMultipartUploaded",
                "ReplicationStatus",
                "EncryptionStatus",
                "ObjectLockRetainUntilDate",
                "ObjectLockMode",
                "ObjectLockLegalHoldStatus",
            ],
            "Schedule": {"Frequency": "Weekly"},
        },
    )
