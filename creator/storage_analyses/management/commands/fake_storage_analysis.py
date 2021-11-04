import json
import logging
import random
from pprint import pformat, pprint

import pandas
import factory
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from creator.storage_analyses.models import StorageAnalysis, FileAudit
from creator.storage_analyses.factories.data import make_files
from creator.storage_analyses.factories.compute import compute_storage_analysis
from creator.studies.models import Study

logger = logging.getLogger(__name__)


def nan_to_none(row, key):
    val = row.get(key)
    if pandas.isnull(val):
        return None
    else:
        return val


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

    def handle(self, *args, **options):
        """
        Make fake storage analysis and inject into db
        """
        # Make fake data
        uploads, inventory = make_files(
            options["n_upload_manifests"], options["n_files"]
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
            # Compute storage analysis stats
            stats, file_audit_df = compute_storage_analysis(uploads, inventory)
            file_audit_df.to_csv("file_audits.tsv", sep="\t", index=False)
            sa.stats = stats
            sa.save()

            logger.info(
                f"{verb} storage analysis {sa.id}:\n"
                f"{pformat(stats)}"
            )
            # Create file audits
            logger.info("Updating file audits table ...")
            sa.file_audits.all().delete()
            for i, row in file_audit_df.iterrows():
                fa = FileAudit(
                    source_filename=nan_to_none(row, "Source File Name"),
                    expected_url=nan_to_none(row, "Url"),
                    expected_hash=nan_to_none(row, "Source Hash"),
                    actual_hash=nan_to_none(row, "Hash"),
                    expected_size=nan_to_none(row, "Source Size"),
                    actual_size=nan_to_none(row, "Size"),
                    hash_algorithm=nan_to_none(row, "Hash Algorithm"),
                    result=nan_to_none(row, "Status"),
                )
                fa.save()
                logger.info(f"Added file audit for {fa.source_filename}")
                sa.file_audits.add(fa)
            sa.refreshed_at = timezone.now()
            sa.save()
        except Exception as e:
            logger.exception(
                "Something went wrong in computing the "
                "storage analysis"
            )
        else:
            logger.info("Complete")
