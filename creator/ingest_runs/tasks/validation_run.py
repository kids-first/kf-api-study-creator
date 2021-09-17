from collections import defaultdict
from typing import List, Dict, Optional
import os
import jsonpickle
import logging
from pprint import pformat
import sys

import pandas
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
from creator.studies.models import Study
from creator.files.models import Version
from creator.data_templates.models import TemplateVersion
from creator.analyses.file_types import FILE_TYPES
from creator.analyses.analyzer import extract_data

S3_STORAGE = "django_s3_storage.storage.S3Storage"

logger = logging.getLogger(__name__)


class ExtractDataError(Exception):
    """
    Raise when something goes wrong in creator.analyses.analyzer.extract_data
    """
    pass


def version_display(version):
    """
    Helper to display version id and file name for log statements
    """
    return f"{version.pk}: {version.file_name}"


def generate_mapper(
    template_versions: List[TemplateVersion]
) -> Dict[str, str]:
    """
    Generate a mapping dict that maps columns in the study templates to
    template keys. This will be used when mapping source file columns to
    template keys in preparation for file validation
    """
    # Create a map of template columns to template keys
    # Also add a mapping of template keys to template keys in case the source
    # file has already been mapped to the template keys
    template_keys = set()
    columns_to_keys = {}
    for tv in template_versions:
        for field in tv.field_definitions["fields"]:
            key = field.get("key")
            if key:
                template_keys.add(key)
                columns_to_keys[field["label"]] = key
                columns_to_keys[key] = key

    # Check for duplicate mappings (multiple template columns map to the same
    # template key) and log them since this typically shouldn't happen but if
    # it does, it could mean improperly configured templates
    reverse_mapping = defaultdict(set)
    for col, key in columns_to_keys.items():
        if col not in template_keys:
            reverse_mapping[key].add(col)
    duplicates = {
        key: cols
        for key, cols in reverse_mapping.items()
        if len(cols) > 1
    }
    if duplicates:
        logger.warning(
            "Found multiple columns in template(s) that map to the same "
            f"template key:\n{pformat(duplicates)}. This could indicate "
            "improperly configured templates"
        )

    return columns_to_keys


def map_column(in_col: str, mapper: Dict[str, str]) -> Optional[str]:
    """
    Map a column in a source file to a template key

    The mapper dict contains a mapping of template columns to template
    keys

    1. (Not Implemented Yet) Try to fuzzy match the src file column to a
    template column
    2. Map result column from 1 to a template key
    """
    return mapper.get(in_col.strip())


def clean_and_map(
    version: Version, mapper: Dict[str, str]
) -> pandas.DataFrame:
    """
    Extract tabular data from a file version into a pandas.DataFrame. Then
    map the DataFrame columns to the file's template keys. This produces a
    DataFrame with standard columns that can be recognized by the validator
    """
    logger.info(
        f"Attempting to map file {version_display(version)} to template keys"
    )
    # Extract file content into a DataFrame
    try:
        df = pandas.DataFrame(extract_data(version))
    except Exception as e:
        er_msg = (
            f"Error in parsing {version_display(version)} "
            "content into a DataFrame."
        )
        raise ExtractDataError from e

    # Try to map as many of the input columns to template keys
    mapped_cols = {c: map_column(c, mapper) for c in df.columns}
    mapped_df = df.rename(columns=mapped_cols, errors="ignore")
    mapped_df = mapped_df[[c for c in mapped_df.columns if c]]

    # Drop duplicate columns (caused by potential multiple src columns
    # that map to the same output column)
    mapped_df = mapped_df.loc[:, ~mapped_df.columns.duplicated()]

    logger.info(
        f"Mapped file version {version_display(version)}:\n"
        f"{pformat(mapped_cols)}"
    )
    return mapped_df


def validate_file_versions(validation_run: ValidationRun) -> dict:
    """
    Load ValidationRun.versions into DataFrames, extract data from each
    version, clean and map the data before passing it to the validator
    """
    versions = validation_run.versions.all()
    logger.info(f"Begin validating file versions: {pformat(list(versions))}")

    # Load study templates
    study = validation_run.data_review.study
    template_versions = study.template_versions.all()
    if len(template_versions) == 0:
        raise TemplateVersion.DoesNotExist(
            "Unable to run validation without templates. The study "
            f"{study.pk} does not have any templates assigned to it"
        )

    # Generate mapping from template columns to template keys
    mapper = generate_mapper(template_versions)
    if not mapper:
        raise ValueError(
            f"Unable to run validation. Study {study.pk} templates do not "
            "have keys defined yet."
        )

    # Clean and map files
    extract_error_count = 0
    empty_df_count = 0
    df_dict = {}
    for version in versions:
        try:
            clean_df = clean_and_map(version, mapper)
        except ExtractDataError as e:
            extract_error_count += 1
            logger.exception(
                "Something went wrong in extracting file version "
                f"{version_display(version)} content into a DataFrame. "
                f"Caused by: {str(e)}"
            )
            continue
        except Exception as e:
            logger.exception(
                "Something went wrong in mapping file version "
                f"{version_display(version)}. Caused by: {str(e)}"
            )
            continue

        if clean_df.empty:
            empty_df_count += 1
        else:
            df_dict[version.pk] = clean_df

    if not df_dict:
        if empty_df_count == len(versions):
            raise ValueError(
                "Unable to run validation. None of the columns in the input "
                f"files matched any of the columns in {study.pk} study "
                "templates"
            )
        elif extract_error_count == len(versions):
            raise ValueError(
                "Unable to run validation. None of the input file formats "
                "are valid for data validation"
            )
        else:
            raise ValueError(
                "Unable to run validation. None of the input files were able "
                "to be cleaned and mapped"
            )

    # Run validation
    try:
        results = DataValidator().validate(df_dict, include_implicit=True)
    except Exception as e:
        logger.exception(
            "Something went wrong while running the data validator"
        )
        raise

    return results


def build_report(results: dict) -> str:
    """
    Build a human friendly markdown report from the validation results dict
    """
    logger.info("Building validation report from validation results")

    rbuilder = MarkdownReportBuilder(setup_logger=False)
    rbuilder.logger = logger

    # Reformat the version references into human friendly names
    # "FV_00000000" -> "participant_conditions.csv: FV_00000000"
    versions = (
        Version.objects.select_related("root_file")
        .only("root_file__file_type")
        .filter(kf_id__in=set(results["files_validated"]))
        .all()
    )
    friendly_names = [
        version_display(version) for version in versions
    ]
    results["files_validated"] = friendly_names

    logger.info(
        f"Finished validation, building report for: {pformat(friendly_names)}"
    )

    return rbuilder._build(results)


def validation_summary(results: ValidationResultset) -> tuple:
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


def serialize_results(results: dict) -> str:
    """
    Use jsonpickle to serialize the validation results dict to JSON

    This preserves the tuples which are used to represent col name, val pairs
    """
    # Convert deques to lists because JSON serialized deques
    # make it hard to read the JSON file
    for result_dict in results["validation"]:
        result_dict["errors"] = list(result_dict["errors"])

    return jsonpickle.encode(results, indent=2, keys=True)


def upload_validation_files(
    results: dict, report_md: str, resultset: ValidationResultset
) -> None:
    """
    Helper to upload validation report/result files to the appropriate
    storage location
    """
    file_contents = {
        "report_file": (report_md, ValidationResultset.report_filename),
        "results_file": (results, ValidationResultset.results_filename),
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


def persist_results(
    results: dict, report_md: str, validation_run: ValidationRun
) -> ValidationResultset:
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
        logger.info("Creating new validation result set")
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
    except Exception as e:
        vr.success = False
        vr.fail(error_msg=str(e))
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
    logger.info(f"Canceling validation run {vr.pk}...")
    vr.cancel()
    vr.save()
