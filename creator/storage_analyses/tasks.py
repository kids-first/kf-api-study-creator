import os
import logging
import requests
from pprint import pprint

import pandas
from django.conf import settings

from creator.decorators import task
from creator.files.models import Version
from creator.analyses.analyzer import extract_data
from creator.dewrangle.client import DewrangleClient
from kf_lib_data_ingest.common.io import read_df

DATAFRAME_CHUNK_SIZE = 100
KNOWN_FORMATS = {
    ".csv": {"reader": pandas.read_csv, "sep": ","},
    ".tsv": {"reader": pandas.read_csv, "sep": "\t"},
    ".txt": {"reader": pandas.read_csv, "sep": None},
}
FILE_UPLOAD_MANIFEST_SCHEMA = {
    "required": [
        "Source File Name",
        "Hash",
        "Hash Algorithm",
        "Size",
    ],
    "optional": [
        "Patient IDs",
        "Specimen IDs"
    ]
}

logger = logging.getLogger(__name__)


class ExtractDataError(Exception):
    pass


def is_file_upload_manifest(version):
    """
    Check whether this file version conforms to the File Upload Manifest schema
    """
    header = {
        "_".join(c.split(" ")).lower()
        for c in read_df(version.key, nrows=0).columns
    }
    expected = {"_".join(c.split(" ")).lower()
                for c in FILE_UPLOAD_MANIFEST_SCHEMA["required"]}
    return expected <= header


def chunked_dataframe_reader(version):
    """
    Read a tabular file into chunks of Dataframes and yield chunks
    """
    # Need to set storage location for study bucket if using S3 backend
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        if version.study is not None:
            study = version.study
        elif version.root_file is not None:
            study = version.root_file.study
        else:
            raise GraphQLError("Version must be part of a study.")

        version.key.storage = S3Storage(aws_s3_bucket_name=study.bucket)

    # Check file format
    _, ext = os.path.splitext(version.key.name)
    if ext not in KNOWN_FORMATS:
        raise IOError(
            "Unsupported file format. Unable to read file upload manifest: "
            f"{version.pk} {version.file_name}"
        )

    # Read file into chunks (DataFrames)
    reader = KNOWN_FORMATS[ext]["reader"]
    delim = KNOWN_FORMATS[ext]["sep"]
    try:
        for i, chunk in enumerate(
            reader(version.key, sep=delim, chunksize=DATAFRAME_CHUNK_SIZE)
        ):
            logger.info(
                f"Reading {DATAFRAME_CHUNK_SIZE} rows from "
                f"{version.file_name} into DataFrame"
            )
            yield chunk
    except Exception as e:
        er_msg = (
            f"Error in parsing {version.pk}: {version.file_name}"
            " content into a DataFrame."
        )
        raise ExtractDataError from e


def dataframe_to_invoices(df):
    """
    Helper to convert a file upload manifest DataFrame into a list of
    FileUploadInvoice dicts in preparation to send to Dewrangle API
    """
    extract_cols = {
        c: "_".join(c.strip().split(" ")).lower()
        for c in (
            FILE_UPLOAD_MANIFEST_SCHEMA["required"] +
            FILE_UPLOAD_MANIFEST_SCHEMA["optional"]
        )
    }
    # Clean up col names
    df = df.rename(columns=extract_cols, errors="ignore")
    # Extract only what we need to create file upload invoices
    df = df[[c for c in extract_cols.values() if c in df.columns]]
    mapping = {
        "source_file_name": "fileName",
        "hash": "hash",
        "hash_algorithm": "hashAlgorithm",
        "size": "size",
        "patient_ids": "patientIds",
        "specimen_ids": "specimenIds"
    }

    return df.rename(columns=mapping).to_dict(orient="records")


@task("push_to_dewrangle")
def push_to_dewrangle(version_id):
    """
    Push the records in a file upload manifest to the Dewrangle API
    where they will processed to produce an audit report of files in
    cloud storage
    """
    study_id = "U3R1ZHk6Y2t3djY2NHBzMDA3MjJsNmpjajQydHY4aw=="
    try:
        version = Version.objects.get(pk=version_id)
        dewrangle = DewrangleClient()
        for df in chunked_dataframe_reader(version):
            logger.info(
                f"Submitting {df.shape[0]} file upload invoices to"
                f" {dewrangle.url}"
            )
            result = dewrangle.bulk_create_file_upload_invoices(
                # version.study.pk,
                study_id,
                dataframe_to_invoices(df)
            )
            logger.info(
                f"Success. Created: {result['created']} invoices. Total:"
                f" {result['total']} invoices"
            )

    except Exception as e:
        # TODO Set Version.submitted_for_audit = fail
        raise

    # TODO
    # set Version.submitted_for_audit = completed
