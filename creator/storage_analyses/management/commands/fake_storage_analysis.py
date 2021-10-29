import json
import logging
import random
from pprint import pformat

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import factory

from creator.storage_analyses.models import StorageAnalysis
from creator.storage_analyses.factories.factory import StorageAnalysisFactory
from creator.storage_analyses.factories.data import make_files
from creator.storage_analyses.factories.compute import compute_storage_analysis
from creator.studies.models import Study

logger = logging.getLogger(__name__)


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
        # Compute storage analysis stats
        stats, file_audit_df = compute_storage_analysis(uploads, inventory)

        # Persist storage analysis
        study_id = options["study_id"]

        # Create if storage analysis doesn't exist for study
        study = Study.objects.get(pk=study_id)
        sa = StorageAnalysis.objects.filter(study=study).first()
        verb = "Updated"
        if not sa:
            verb = "Created"
            sa = StorageAnalysis(study=study)

        sa.refreshed_at = timezone.now()
        sa.stats = stats
        sa.save()

        logger.info(
            f"{verb} storage analysis {sa.id}:\n"
            f"{stats}"
        )
