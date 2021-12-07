import logging
import os
from io import BytesIO
from pprint import pprint

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
import pandas

from creator.organizations.factories import (
    OrganizationFactory,
    Organization
)
from creator.studies.factories import StudyFactory, Study
from creator.files.models import Version, File as StudyFile
from creator.storage_analyses.tasks import (
    is_file_upload_manifest,
    push_to_dewrangle
)

MANIFEST_FILE = "demo/data/cbtn-file-upload-manifest.tsv"
logger = logging.getLogger(__name__)


def update_version_content(df, file_version):
    """
    Helper to update the file version's content
    """
    stream = BytesIO()
    df.to_csv(stream, sep="\t", index=False)
    stream.seek(0)
    file_version.key.save("file_upload_manifest.tsv", File(stream))
    file_version.save()


def prep_file(manifest_fp=MANIFEST_FILE):
    """
    Create a study, file, version with a file upload manifest
    """
    org = Organization.objects.first()
    study = Study.objects.get(pk="SD_ME0WME0W")

    # Delete existing files
    study.files.all().delete()
    file_ = StudyFile(name="FileUploadManifest", study=study)
    file_.save()
    version = Version(
        root_file=file_, study=study, size=123,
        file_name="file_upload_manifest.tsv"
    )
    version.save()

    # Create version w upload manifest
    df = pandas.read_csv(manifest_fp, sep="\t")
    update_version_content(df, version)

    logger.info(f"Prepped study, file and version: {version}")
    return version


class Command(BaseCommand):
    help = 'Create file upload manifest for testing dewrangle integration'

    def add_arguments(self, parser):
        parser.add_argument('--manifest_file', help='Path to manifest file')

    def handle(self, *args, **options):
        """
        Fake a version upload so we can test the push to dewrangle
        functionality
        """
        # Create version with upload manifest content
        version = prep_file()

        # Pretend to call upload version
        if (
            settings.FEAT_DEWRANGLE_INTEGRATION and
            is_file_upload_manifest(version)
        ):
            logger.info(
                f"Queued version {version.kf_id} {version.root_file.name} for"
                " audit processing..."
            )
            push_to_dewrangle(version.pk)
            # django_rq.enqueue(
            #     push_to_dewrangle, version_id=version.pk
            # )
