import boto3
import csv
import datetime
import json
import logging
import smart_open
import django_rq
from collections import defaultdict
from pathlib import Path
from django.conf import settings

from creator.decorators import task
from creator.studies.models import Study
from creator.buckets.models import Bucket, BucketInventory

logger = logging.getLogger(__name__)

SUMMARY_VERSION = 8


def condense_ext(r):
    """
    'Condenses' a file extension by removing any unecessary components. Eg:
    .vep.vcf.gz.tbi -> .vcf.gz.tbi
    .gatk.filtered.FINAL.vcf.gz -> .vcf.gz
    """
    d = [
        ".g.vcf.gz.tbi",
        ".g.vcf.gz",
        ".vcf.gz.tbi",
        ".vcf.gz",
        ".tsv.gz",
        ".maf",
        ".png",
        ".html",
        ".pdf",
        ".txt.gz",
        ".txt",
        ".bam",
        ".log.gz",
        ".log",
    ]
    for ext in d:
        if r.endswith(ext):
            return ext
    return ""


def top_n(d, n=10):
    """
    Return a dictionary consisting of the n largest items by value from the
    original dictionary
    """
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=True)[:n])


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

    total_queued = 0
    for bucket in buckets:
        prefix = f"inventories/{bucket.name}/StudyBucketInventory/"

        result = client.list_objects(
            Bucket=settings.STUDY_BUCKETS_INVENTORY_LOCATION,
            Prefix=prefix,
            Delimiter="/",
        )

        # Compile all the sub-prefixes within the 'StudyBucketInventory' prefix
        # Each sub-prefix is a date containing a 'manifest.json' and md5 sum
        # except for 'data' and 'hive' prefixes which contain actual the actual
        # inventory data dumps
        inventory_prefixes = [
            pref.get("Prefix") for pref in result.get("CommonPrefixes", [])
        ]

        queued = import_inventories_for_bucket(bucket, inventory_prefixes)
        total_queued += queued
        if queued > 0:
            logger.info(
                f"Queued {queued} inventories for import for '{bucket.name}'"
            )
    logger.info(
        f"Scanned {len(buckets)} buckets for new inventories and queued "
        f"{total_queued} inventories for import"
    )


def import_inventories_for_bucket(bucket, inventories):
    """
    Scan a bucket's inventory history for inventories that need to be imported
    and queue work to import that inventory file.

    Inventories that have imported=False may have failed previously and will
    be re-invoked for import.
    Inventories that do not have a summary with the latest version will be
    invoked for re-processing.
    """
    folders_by_date = {}
    for inventory in inventories:
        try:
            date = datetime.datetime.strptime(
                inventory.split("/")[-2], "%Y-%m-%dT%H-%MZ"
            )
            date = date.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            # Skip this inventory if we could not parse a date in it
            continue

        folders_by_date[date] = inventory

    logger.debug(
        f"Found {len(folders_by_date)} inventories for bucket '{bucket.name}"
    )

    # Keep track of how many inventories are being queued for import
    queued = 0
    for date, prefix in folders_by_date.items():
        if not (
            ("sd-" in bucket.name or "seq-" in bucket.name) and (date.day < 7)
        ):
            continue
        # Try to first resolve a BucketInventory to see if we've already
        # imported the inventory at this prefix for the given date
        # NB: The inventory must have been successfully imported and the
        # summary schema version must be on par with the current version
        if BucketInventory.objects.filter(
            bucket=bucket,
            creation_date=date,
            imported=True,
            summary__summary_version=SUMMARY_VERSION,
        ):
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

        inventory, created = BucketInventory.objects.get_or_create(
            creation_date=date,
            bucket=bucket,
            imported=False,
            defaults={"manifest": manifest},
        )
        inventory.save()

        queue = django_rq.get_queue("aws", default_timeout=300)
        queue.enqueue(import_inventory, inventory_id=inventory.pk, ttl=600)
        queued += 1
    return queued


def generate_summary(reader):
    """
    Generate summary aggregations for a file stream.

    A summary contains sum aggregations for both object count and disk size.
    Within each aggregation, there are groupings by is_latest, storage_class,
    replication_status, encryption_status, and top level folder.

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
        top_prefix = row.get("Key").split("/")
        if len(top_prefix) > 1:
            top_prefix = top_prefix[0] + "/"
        else:
            top_prefix = "/"

        extension = condense_ext("".join(Path(row.get("Key", "")).suffixes))
        if len(extension) == 0:
            extension = None

        try:
            size = int(row.get("Size"))
        except ValueError:
            size = 0

        size_aggs["is_latest"][is_latest] += size
        size_aggs["storage_class"][storage_class] += size
        size_aggs["replication_status"][replication_status] += size
        size_aggs["encryption_status"][encryption_status] += size
        size_aggs["top_folder"][top_prefix] += size
        if extension is not None:
            size_aggs["extension"][extension] += size
        total_size += size

        count_aggs["is_latest"][is_latest] += 1
        count_aggs["storage_class"][storage_class] += 1
        count_aggs["replication_status"][replication_status] += 1
        count_aggs["encryption_status"][encryption_status] += 1
        count_aggs["top_folder"][top_prefix] += 1
        if extension is not None:
            count_aggs["extension"][extension] += 1
        total_count += 1

    # Filter down to only the 10 most/largest folders and extensions
    size_aggs["top_folder"] = top_n(size_aggs["top_folder"], 20)
    count_aggs["top_folder"] = top_n(count_aggs["top_folder"], 20)
    size_aggs["extension"] = top_n(size_aggs["extension"], 20)
    count_aggs["extension"] = top_n(count_aggs["extension"], 20)

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
