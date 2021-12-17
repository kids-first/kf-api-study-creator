import os
import logging

import pandas
import django_rq
from django.conf import settings
from django.db import IntegrityError

from creator.decorators import task
from creator.studies.models import Study
from creator.files.models import Version
from creator.storage_analyses.models import (
    UNIQUE_CONSTRAINT,
    FILE_UPLOAD_MANIFEST_SCHEMA,
    ExpectedFile,
    AuditState
)
from creator.storage_analyses import utils
from creator.dewrangle.client import DewrangleClient
from pprint import pprint

EXPECTED_FILE_BATCH_SIZE = 1000
REQUIRED_COLS = FILE_UPLOAD_MANIFEST_SCHEMA["required"]
OPTIONAL_COLS = FILE_UPLOAD_MANIFEST_SCHEMA["optional"]

logger = logging.getLogger(__name__)


def _bulk_update_audit_state(expected_files, method_name):
    """
    Bulk update the audit state for a batch of ExpectedFiles via
    its state transition method
    """
    for f in expected_files:
        state_transition = getattr(f, method_name)
        state_transition()

    return ExpectedFile.objects.bulk_update(
        expected_files, fields=["audit_state"]
    )


def _dataframe_to_expected_files(df, study):
    """
    Helper to convert a file upload manifest DataFrame into a list of
    ExpectedFile dicts in preparation to send to Dewrangle API
    """
    extract_cols = REQUIRED_COLS + OPTIONAL_COLS

    # Clean up col names
    renamed = {}
    for c in df.columns:
        new_c = "_".join(c.strip().split(" ")).lower()
        if new_c in extract_cols:
            renamed[c] = new_c
    df = df.rename(columns=renamed)

    # Collapse additional columns into a custom_fields column
    custom_cols = [c for c in df.columns if c not in extract_cols]
    df["custom_fields"] = df.apply(
        lambda row: {k: v for k, v in row.items() if k in custom_cols}, axis=1
    )

    # Add study_id column
    df["study_id"] = study.pk

    # Extract only what we need to create expected files
    extract_cols.extend(["custom_fields", "study_id"])
    df = df[[c for c in extract_cols if c in df.columns]]

    # Try weeding out duplicate records early
    duplicates = df.duplicated(subset=UNIQUE_CONSTRAINT)
    dups = df[duplicates].shape[0]
    df = df[~duplicates]
    if dups:
        logger.warning(
            f"Dropping {dups} duplicate rows based on "
            f"unique constraint: {UNIQUE_CONSTRAINT}"
        )

    # Drop any rows where required cols are null
    missing_required = df[REQUIRED_COLS].isnull().any(axis=1)
    req = df[missing_required].shape[0]
    df = df[~missing_required]
    if req:
        logger.warning(
            f"Dropping {req} rows due to one or "
            f"more required fields: {REQUIRED_COLS} being null"
        )

    return df.to_dict(orient="records")


@task("prepare_audit_submission")
def prepare_audit_submission(version_id):
    """
    Read the content of a file upload manifest and produce a ExpectedFile
    for each row

    Save ExpectedFiles to the study so they can later be submitted to the
    auditing system (Dewrangle) to verify that the file exists in the 
    study's cloud storage
    """
    logger.info(
        f"Preparing expected files in {version_id} for submission to "
        "audit system"
    )
    version = Version.objects.get(pk=version_id)
    study = version.root_file.study
    try:
        total_upserted = 0
        total_rows = 0

        # Iterate over large DataFrame in smaller DataFrame chunks and
        # Submit rows in each DataFrame chunk to bulk upsert ExpectedFiles
        for df in utils.chunked_dataframe_reader(
            version,
            batch_size=EXPECTED_FILE_BATCH_SIZE
        ):
            logger.info(
                f"Reading {EXPECTED_FILE_BATCH_SIZE} rows from "
                f"{version.file_name} into DataFrame"
            )

            total_rows += df.shape[0]

            upserted_files = utils.bulk_upsert_expected_files(
                _dataframe_to_expected_files(df, study),
            )

            total_upserted += len(upserted_files)

            logger.info(
                f"Upserted {total_upserted} expected_files. Total rows "
                f"processed: {total_rows} in file upload manifest: "
                f"{version_id} ..."
            )
    except Exception as e:
        logger.exception(
            f"Something went wrong while processing version {version_id} "
            "in prepration for audit submission"
        )
        version.fail_audit_prep()
        version.save()
        raise

    version.complete_audit_prep()
    version.save()

    django_rq.enqueue(
        submit_study_for_audit, study.pk
    )


@task("submit_study_for_audit")
def submit_study_for_audit(study_id):
    """
    Submit a Study's ExpectedFiles to the auditing system (Dewrangle)
    for audit processing

    Only submit the files that have not started or have previously failed
    submission
    """
    dewrangle = DewrangleClient()
    study = Study.objects.get(pk=study_id)

    states = [AuditState.NOT_SUBMITTED, AuditState.FAILED]
    count = ExpectedFile.objects.filter(
        audit_state__in=states, study=study
    ).count()

    if not count:
        logger.info(
            "There are no more expected files to submit for study "
            f"{study_id}"
        )
        return

    # Upsert study/org in Dewrangle
    results = dewrangle.upsert_organization(study.organization)
    logger.info(
        f"Upserted organization {study.organization.dewrangle_id}"
        f" in dewrangle"
    )
    dewrangle.upsert_study(study)
    logger.info(
        f"Upserted study {study.dewrangle_id} in dewrangle"
    )

    logger.info(
        f"Begin submitting expected files for study {study_id} "
        f"to audit system @ {dewrangle.url}"
    )
    batched_expected_files = utils.batched_queryset_iterator(
        ExpectedFile.objects.filter(
            audit_state__in=states, study=study
        ).all(),
        batch_size=EXPECTED_FILE_BATCH_SIZE
    )
    for batch in batched_expected_files:
        # Set audit state to submitting
        _bulk_update_audit_state(batch, "start_submission")
        try:
            payloads = [
                {
                    "location": expected_file.file_location,
                    "hash": expected_file.hash,
                    "hashAlgorithm": expected_file.hash_algorithm.upper(),
                    "size": expected_file.size,
                }
                for expected_file in batch
            ]
            result = dewrangle.bulk_upsert_expected_files(
                study.dewrangle_id, payloads
            )
            logger.info(
                f"Successfully submitted expected_files: {result['upserted']} "
                f"Total expected_files: {result['total']} "
            )
        except Exception as e:
            logger.exception(
                "Failed submitting batch of expected_files to audit system @"
                f" {dewrangle.url}"
            )

            # Set audit state to completed submission
            _bulk_update_audit_state(batch, "fail_submission")

            raise

        # Set audit state to completed submission
        _bulk_update_audit_state(batch, "complete_submission")
