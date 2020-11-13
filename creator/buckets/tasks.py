import boto3
import csv
import datetime
import json
import logging
import smart_open
import django_rq
from collections import defaultdict
from django.conf import settings

from creator.decorators import task
from creator.studies.models import Study
from creator.buckets.models import Bucket, BucketInventory

logger = logging.getLogger(__name__)

SUMMARY_VERSION = 1


@task(job="sync_inventories")
def sync_inventories():
    """
    Scan for any un-imported inventories and launch new jobs to process them.
    """
    client = boto3.client("s3")

    buckets = Bucket.objects.all()

    inventories_location = (
        settings.STUDY_BUCKETS_INVENTORY_LOCATION + "/inventories"
    )

    for bucket in buckets:
        logger.info(f"Scanning bucket '{bucket.name}' for new inventories")

        prefix = f"inventories/{bucket.name}/StudyBucketInventory/"

        result = client.list_objects(
            Bucket=settings.STUDY_BUCKETS_INVENTORY_LOCATION,
            Prefix=prefix,
            Delimiter="/",
        )

        folders_by_date = {}

        for pref in reversed(result.get("CommonPrefixes", [])):
            prefix = pref.get("Prefix")
            try:
                date = datetime.datetime.strptime(
                    prefix.split("/")[-2], "%Y-%m-%dT%H-%MZ"
                )
                date = date.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                continue
            folders_by_date[date] = prefix

        logger.debug(
            f"Found {len(folders_by_date)} inventories for bucket "
            f"'{bucket.name}"
        )

        queued = 0
        for date, prefix in folders_by_date.items():
            # Try to first resolve an BucketInventory to see if we've already
            # imported the inventory at this prefix for the given date
            if BucketInventory.objects.filter(
                bucket=bucket, creation_date=date
            ).exists():
                continue
            # Continue with setting up the inventory
            try:
                with smart_open.open(
                    f"s3://{settings.STUDY_BUCKETS_INVENTORY_LOCATION}/{prefix}"
                    "manifest.json"
                ) as f:
                    manifest = json.load(f)
            except Exception as exc:
                logger.error(f"Problem reading file: {exc}")
                continue

            inventory = BucketInventory(
                creation_date=date,
                bucket=bucket,
                manifest=manifest,
                imported=False,
            )
            inventory.save()
            django_rq.enqueue(
                import_inventory, inventory_id=inventory.pk, ttl=600
            )

        logger.info(
            f"Queued import of {queued} inventories for bucket '{bucket.name}'"
        )


def generate_summary(reader):
    """
    Generate summary aggregations for a file stream.

    A summary contains sum aggregations for both object count and disk size.
    Within each aggregation, there are groupings by is_latest, storage_class,
    replication_status, and encryption_status.

    The summary also includes a version number which can be incremented in the
    case that summaries ever need to be re-generated.
    """

    size_aggs = defaultdict(lambda: defaultdict(int))
    count_aggs = defaultdict(lambda: defaultdict(int))

    total_size = 0
    total_count = 0

    def is_directory(row):
        if (
            row["Key"].endswith("/")
            and row["Size"] == "0"
            and row["VersionId"] == ""
        ):
            return True
        return False

    i = 0
    for row in reader:
        if is_directory(row):
            continue
        i += 1
        is_latest = row.get("IsLatest")
        storage_class = row.get("StorageClass")
        replication_status = row.get("ReplicationStatus")
        encryption_status = row.get("EncryptionStatus")

        try:
            size = int(row.get("Size"))
        except ValueError:
            size = 0

        size_aggs["is_latest"][is_latest] += size
        size_aggs["storage_class"][storage_class] += size
        size_aggs["replication_status"][replication_status] += size
        size_aggs["encryption_status"][encryption_status] += size
        total_size += size

        count_aggs["is_latest"][is_latest] += 1
        count_aggs["storage_class"][storage_class] += 1
        count_aggs["replication_status"][replication_status] += 1
        count_aggs["encryption_status"][encryption_status] += 1
        total_count += 1

    logger.info(f"Aggregated {i} records")
    return {
        "summary_version": SUMMARY_VERSION,
        "count": count_aggs,
        "size": size_aggs,
        "total_count": total_count,
        "total_size": total_size,
    }


@task(job="import_inventory")
def import_inventory(inventory_id):
    """
    Imports an inventory at a given location
    """
    inventory = BucketInventory.objects.get(pk=inventory_id)
    logger.info(
        f"About to process inventory '{inventory.pk}' of bucket "
        f"'{inventory.bucket.name}' generated on {inventory.creation_date}"
    )
    location = inventory.manifest.get("files")[0].get("key")
    header = inventory.manifest.get("fileSchema").split(", ")

    with smart_open.open(
        f"s3://{settings.STUDY_BUCKETS_INVENTORY_LOCATION}/{location}"
    ) as f:
        reader = csv.DictReader(f, fieldnames=header)
        summary = generate_summary(reader)

    inventory.summary = summary
    inventory.imported = True
    inventory.save()

    logger.info(f"Completed import for inventory '{inventory.pk}")
