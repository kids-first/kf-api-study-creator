import os
import json
import jsonpickle
import logging
from pprint import pformat, pprint

import pandas
import django_rq
from django.conf import settings
from django.core.files.base import ContentFile
from django_s3_storage.storage import S3Storage

from kf_lib_data_ingest.etl.extract.utils import Extractor
from kf_lib_data_ingest.validation.data_validator import (
    Validator as DataValidator,
)
from kf_lib_data_ingest.validation.reporting.markdown import (
    MarkdownReportBuilder,
)

from creator.decorators import task
from creator.ingest_runs.models import ValidationRun, ValidationResultset
from creator.files.models import Version
from creator.analyses.file_types import FILE_TYPES
from creator.analyses.analyzer import extract_data

S3_STORAGE = "django_s3_storage.storage.S3Storage"

logger = logging.getLogger(__name__)


def clean_and_map(version):
    """
    Load tabular data from file version into a DataFrame and then use
    ingest lib's extraction utility to clean the values and map the column
    names to the standard set of concepts expected by the validator
    """
    logger.info(f"Performing extraction to clean and map file {version}")

    # Load ingest extract operations for this file
    if not version.root_file:
        raise Exception(
            f"Validation failed. Version {version} missing root_file"
        )
    ec = version.extract_config_path
    if not ec:
        logger.warning(
            f"⚠️  Could not find an extract config for file version {version} "
            f"with file type: {version.root_file.file_type}. This file will "
            "not be included in validation."
        )
        return None
    # Extract file content into a DataFrame
    try:
        df = pandas.DataFrame(extract_data(version))
    except Exception as e:
        logger.error(
            "Validation failed! Error in parsing {version} content into "
            "a DataFrame."
        )
        raise

    logger.info(
        f"Applied extract config {os.path.split(ec)[-1]} for file "
        f"{version.root_file.file_type}, {version.kf_id}"
    )

    ext = Extractor()
    ext.logger = logger

    return ext.extract(df, ec)


def validate_file_versions(validation_run):
    """
    Load ValidationRun.versions into DataFrames, extract data from each
    version, clean and map the data before passing it to the validator
    """
    versions = validation_run.versions.all()
    logger.info(
        f"Begin validating file versions: {pformat(list(versions))}"
    )
    # Clean and map source data
    df_dict = {}
    for version in versions:
        clean_df = clean_and_map(version)
        if isinstance(clean_df, pandas.DataFrame):
            df_dict[version.kf_id] = clean_df

    # None of the input files had templates
    if not df_dict:
        raise Exception(
            "Validation failed! Validation only runs on files that conform "
            "to expedited file types. None of the input files conformed to "
            "any of the available expedited file types"
        )

    # Validate
    return DataValidator().validate(df_dict, include_implicit=True)


def build_report(results):
    """
    Build a human friendly markdown report from the validation results dict
    """
    logger.info("Building validation report from validation results")

    rbuilder = MarkdownReportBuilder(setup_logger=False)
    rbuilder.logger = logger

    # Reformat the version references into human friendly names
    # "FV_00000000" -> "Participant Conditions, FV_00000000"
    friendly_names = []
    versions = (
        Version.objects.select_related("root_file")
        .only("root_file__file_type")
        .filter(kf_id__in=set(results["files_validated"])).all()
    )
    for version in versions:
        type_name = FILE_TYPES[version.root_file.file_type]["name"]
        friendly_names.append(f"{type_name}, {version.kf_id}")
    results["files_validated"] = friendly_names

    logger.info(
        f"Finished validation, building report for: {pformat(friendly_names)}"
    )

    return rbuilder._build(results)


def validation_summary(results):
    """
    Scan validation results dict and tally up the validation tests that
    passed, failed, and did not run
    """
    failed = 0
    passed = 0
    did_not_run = 0
    for r in results["validation"]:
        if not r["is_applicable"]:
            did_not_run += 1
        elif r["errors"]:
            failed += len(r["errors"])
        else:
            passed += 1
    return passed, failed, did_not_run


def serialize_results(results):
    """
    Use jsonpickle to serialize the validation results dict to JSON

    This preserves the tuples which are used to represent col name, val pairs
    """
    # Convert deques to lists because JSON serialized deques
    # make it hard to read the JSON file
    for result_dict in results["validation"]:
        result_dict["errors"] = list(result_dict["errors"])

    return jsonpickle.encode(results, indent=2, keys=True)


def upload_validation_files(results, report_md, resultset):
    """
    Helper to upload validation report/result files to the appropriate
    storage location
    """
    file_contents = {
        "report_file": (report_md, ValidationResultset.report_filename),
        "results_file": (results, ValidationResultset.results_filename)
    }
    for attr, (content, fname) in file_contents.items():
        if not content:
            continue

        file_field = getattr(resultset, attr)

        # Use study bucket if storage backend is S3
        if settings.DEFAULT_FILE_STORAGE == S3_STORAGE:
            file_field.storage = S3Storage(
                aws_s3_bucket_name=resultset.data_review.study.bucket
            )
        if fname.endswith("json"):
            content = serialize_results(content)

        # Filename: validation_<report or results>_<data_review.kf_id>.<ext>
        fname, ext = os.path.splitext(fname)
        fname = f"{fname}_{resultset.data_review.kf_id.lower()}{ext}"
        file_field.save(fname, ContentFile(content))

        logger.info(f"Wrote {file_field.name}")


def persist_results(results, report_md, validation_run):
    """
    Create or update the validation resultset with validation summary
    Update the success and progress fields on the validation run
    Upload validation results and report files to storage backend
    """
    # Create or update validation result set with result summary
    resultset = None
    try:
        resultset = validation_run.data_review.validation_resultset
    except ValidationResultset.DoesNotExist:
        logger.info(f"Creating new validation result set")
        resultset = ValidationResultset(data_review=validation_run.data_review)

    passed, failed, did_not_run = validation_summary(results)

    logger.info(
        f"Saving validation result summary: {passed} ✅, {failed} ❌,"
        f"{did_not_run} 🚫"
    )

    resultset.passed = passed
    resultset.failed = failed
    resultset.did_not_run = did_not_run
    validation_run.success = resultset.failed == 0
    validation_run.progress = 1
    validation_run.save()
    resultset.save()

    # Upload validation files
    logger.info("Persisting validation results to storage backend")
    upload_validation_files(results, report_md, resultset)

    return resultset


@task("run_validation")
def run_validation(validation_run_uuid=None):
    """
    Run validation process for the file versions in a ValidationRun
    """
    vr = ValidationRun.objects.get(pk=validation_run_uuid)
    logger.info(
        f"Starting validation run {vr.pk} for data review {vr.data_review.pk}"
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

    logger.info(
        f"Validation run {vr.pk} for data review "
        f"{vr.data_review.pk} complete!"
    )
    vr.complete()
    vr.save()


@task("cancel_validation")
def cancel_validation(validation_run_uuid=None):
    """
    Cancel validation run
    """
    vr = ValidationRun.objects.get(pk=validation_run_uuid)
    logging.info(f"Canceling validation run {vr.pk}...")
    vr.cancel()
    vr.save()
