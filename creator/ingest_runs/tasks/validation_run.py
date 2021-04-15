import os
import logging
import django_rq
from django.conf import settings
from django.core.files.base import ContentFile
from django_s3_storage.storage import S3Storage

from creator.decorators import task
from creator.ingest_runs.models import ValidationRun, ValidationResultset

S3_STORAGE = "django_s3_storage.storage.S3Storage"

logger = logging.getLogger(__name__)


def validate_file_versions(validation_run):
    """
    TODO - Replace later. Currently counts to 10 then returns

    Upload validation results and report files to storage backend
    """
    logger.info(f"Begin validation for {validation_run.versions.all()}")
    results = {}

    import time
    t_end = time.time() + 10
    progress = ""
    while time.time() < t_end:
        time.sleep(1)
        progress += "."
        print(progress)

    return results


def build_report(results):
    """
    TODO - Replace later. Currently returns sample markdown validation report

    Build human friendly validation report from validation results
    """
    logger.info("Building validation report from validation results")

    with open("tests/data/sample_validation_report.md") as report_file:
        report = report_file.read()

    return report


def persist_results(results, report_md, validation_run):
    """
    TODO - Replace later. Currently uploads sample validation report

    Upload validation results and report files to storage backend
    """
    logger.info("Persisting validation results to storage backend")

    # Create or update validation result set
    resultset = None
    try:
        resultset = validation_run.data_review.validation_resultset
    except ValidationResultset.DoesNotExist:
        logger.info(f"Creating new validation result set")
        resultset = ValidationResultset(data_review=validation_run.data_review)

    # TODO - Update the validation resultset failed, passed, did not run
    # from validation results
    resultset.failed = 2
    resultset.passed = 6
    resultset.did_not_run = 49
    validation_run.success = resultset.failed == 0
    validation_run.progress = 1
    validation_run.save()
    resultset.save()

    # Upload validation files
    file_contents = {
        "report_file": (report_md, ValidationResultset.report_filename),
        "results_file": (results, ValidationResultset.results_filename)
    }
    for attr, (content, fname) in file_contents.items():
        if not content:
            continue

        file_field = getattr(resultset, attr)

        # Use study bucket if storage backend is S3
        if (settings.DEFAULT_FILE_STORAGE == S3_STORAGE):
            file_field.storage = S3Storage(
                aws_s3_bucket_name=data_review.study.bucket
            )
        if fname.endswith("json"):
            content = json.dumps(content, indent=2)

        # Filename: validation_<report or results>_<data_review kf id>.<ext>
        fname, ext = os.path.splitext(fname)
        fname = f"{fname}_{validation_run.data_review.kf_id.lower()}{ext}"
        file_field.save(fname, ContentFile(content))
        logger.info(
            f"Wrote {' '.join(attr.split('_'))} to {file_field.path}"
        )

    return resultset


@task("run_validation")
def run_validation(validation_run_uuid=None):
    """
    TODO
    Run validation process for a given set of files.
    """
    vr = ValidationRun.objects.get(pk=validation_run_uuid)
    logging.info(
        f"Starting validation run {vr.pk}"
    )
    vr.start()
    vr.save()
    try:
        results = validate_file_versions(vr)
        report_markdown = build_report(results)
        vrs = persist_results(results, report_markdown, vr)
    except Exception:
        vr.success = False
        vr.fail()
        vr.save()
        raise

    logger.info(f"Validation run {vr.pk} complete!")
    vr.complete()
    vr.save()


@task("cancel_validation")
def cancel_validation(validation_run_uuid=None):
    """
    TODO
    Cancel validation run
    """
    vr = ValidationRun.objects.get(pk=validation_run_uuid)
    logging.info(f"Canceling validation run {vr.pk}...")
    vr.cancel()
    vr.save()
