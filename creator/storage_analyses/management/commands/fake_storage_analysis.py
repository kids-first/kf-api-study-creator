from datetime import timedelta
import json
import logging
import random
from pprint import pformat, pprint

import pandas
import numpy
import factory
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from creator.storage_analyses.models import StorageAnalysis, FileAudit
from creator.storage_analyses.factories.data import make_files, load_dfs
from creator.storage_analyses.factories.compute import compute_storage_analysis
from creator.studies.models import Study

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000
UNIQUE_CONSTRAINT = ["Source File Name", "Source Hash", "Hash", "Url"]


def nan_to_none(row, key):
    val = row.get(key)
    if pandas.isnull(val):
        return None
    else:
        return val


def row_to_file_audit(row, storage_analysis):
    return FileAudit(
        source_filename=nan_to_none(row, "Source File Name"),
        expected_url=nan_to_none(row, "Url"),
        expected_hash=nan_to_none(row, "Source Hash"),
        actual_hash=nan_to_none(row, "Hash"),
        expected_size=nan_to_none(row, "Source Size"),
        actual_size=nan_to_none(row, "Size"),
        hash_algorithm=nan_to_none(row, "Hash Algorithm"),
        result=nan_to_none(row, "Status"),
        storage_analysis=storage_analysis
    )


class Command(BaseCommand):
    help = "Make some fake file upload manifests and s3 inventory and"
    " compute a storage analysis for the given study"

    def add_arguments(self, parser):
        parser.add_argument(
            "--study_id",
            default="SD_ME0WME0W",
            help="kf_id of the study to make the storage analysis for",
            type=str
        )
        parser.add_argument(
            "--n_upload_manifests",
            default=3,
            help="Number of file upload manifests to create",
            type=int
        )
        parser.add_argument(
            "--n_files",
            default=10,
            help="Number of files per file upload manifest",
            type=int
        )
        parser.add_argument(
            "--inventory_filepath",
            help="Path to an S3 inventory file to read in. If "
            "this and --upload_manifests_dir are supplied, then data will "
            "be read in from disk rather than generated",
            type=str
        )
        parser.add_argument(
            "--upload_manifests_dir",
            help="Path to a directory with file upload manifests. If "
            "this and --inventory_filepath are supplied, then data will "
            "be read in from disk rather than generated",
            type=str
        )

    def handle(self, *args, **options):
        """
        Make fake storage analysis and inject into db
        """
        # Read data in if provided
        if options["upload_manifests_dir"] and options["inventory_filepath"]:
            uploads, inventory = load_dfs(
                options["upload_manifests_dir"],
                options["inventory_filepath"]
            )
        # Make fake data
        else:
            uploads, inventory = make_files(
                options["n_upload_manifests"],
                options["n_files"],
                options["study_id"]
            )
        # Create if storage analysis doesn't exist for study
        study_id = options["study_id"]
        study = Study.objects.get(pk=study_id)
        sa = StorageAnalysis.objects.filter(study=study).first()
        verb = "Updated"
        if not sa:
            verb = "Created"
            sa = StorageAnalysis(study=study)

        try:
            # Delete existing file audits
            sa.file_audits.all().delete()

            # Compute storage analysis stats
            stats, file_audit_df = compute_storage_analysis(uploads, inventory)
            sa.scanned_storage_at = timezone.now() - timedelta(days=1)
            sa.stats = stats
            sa.save()

            logger.info(
                f"{verb} storage analysis {sa.id}:\n"
                f"{pformat(stats)}"
            )
            file_audit_df.to_csv("file_audits.tsv", sep="\t", index=False)

            # Create file audits
            logger.info("Updating file audits table ...")

            total = file_audit_df.shape[0]
            n_batches = int(total/BATCH_SIZE) or 1
            total_created = 0
            for bi, df_batch in enumerate(
                numpy.array_split(file_audit_df, n_batches)
            ):
                # Warn when duplicates are found bc they must be dropped
                # prior to bulk create since it cannot operate on the
                # same row twice in the same transaction
                duplicates = df_batch.duplicated(subset=UNIQUE_CONSTRAINT)
                df_batch = df_batch[~duplicates]
                dups = df_batch[duplicates].shape[0]
                if dups:
                    logger.warning(
                        f"Dropping {dups} duplicate rows based on "
                        f"unique constraint: {UNIQUE_CONSTRAINT}"
                    )

                batch_audits = []
                for i, row in df_batch.iterrows():
                    fa = row_to_file_audit(row, sa)
                    batch_audits.append(fa)
                    # logger.info(
                    #     f"Adding file audit {bi + i}/{total} for "
                    #     f"{fa.source_filename}"
                    # )
                created = FileAudit.objects.bulk_create(
                    batch_audits, ignore_conflicts=True
                )
                total_created += len(created)
                logger.info(
                    f"Bulk created {total_created}/{total} file audits")

            sa.refreshed_at = timezone.now()
            sa.save()
        except Exception as e:
            logger.exception(
                "Something went wrong in computing the "
                "storage analysis"
            )
        else:
            logger.info("Complete")
