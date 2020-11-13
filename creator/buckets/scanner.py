import boto3
import logging
import re
from django.conf import settings
from creator.buckets.models import Bucket
from creator.studies.models import Study

logger = logging.getLogger(__name__)

study_re = re.compile(r".+-(sd-[a-z0-9]{8}).*")


def sync_buckets():
    """
    Synchronize buckets in s3 with internal models
    """

    client = boto3.client("s3")
    try:
        buckets = client.list_buckets()["Buckets"]
    except Exception as err:
        logger.error(f"Problem listing buckets in S3: {err}")
        raise

    settings.STAGE = "prd"
    # buckets = [b for b in buckets if f"-{settings.STAGE}-sd-" in b["Name"]]
    buckets = [b for b in buckets]

    logger.info(f"Found {len(buckets)} buckets to update")
    for bucket_info in buckets:
        try:
            bucket = Bucket.objects.get(name=bucket_info["Name"])
        except Bucket.DoesNotExist:
            logger.info(f"Found new bucket {bucket_info['Name']}")
            bucket = Bucket(
                name=bucket_info["Name"],
                created_on=bucket_info["CreationDate"],
            )

        link_study(bucket)

        bucket.deleted = False

        bucket.save()

    db_buckets = {b.name for b in Bucket.objects.filter(deleted=False).all()}
    deleted_buckets = db_buckets - {b["Name"] for b in buckets}
    logger.info(f"Found {len(buckets)} buckets that are no longer in S3")
    for bucket in deleted_buckets:
        bucket = Bucket.objects.get(name=bucket)
        bucket.deleted = True
        bucket.save()


def link_study(bucket):
    """
    Attempts to link a bucket to a study by extracting a kf_id from its name
    """
    study_match = study_re.match(bucket.name)
    if study_match is None:
        return False
    if not study_match.group(1):
        return False

    study_id = study_match.group(1).upper().replace("-", "_")

    try:
        study = Study.objects.get(kf_id=study_id)
    except Study.DoesNotExist:
        logger.info(f"Could not find a study for bucket {bucket.name}")
        return False

    logger.info(f"Linked bucket {bucket.name} to study {study_id}")
    bucket.study = study
    return True
