import os
import logging
from itertools import chain, islice

import pandas
from django.conf import settings
from psqlextra.util import postgres_manager
from psqlextra.query import ConflictAction
from creator.storage_analyses.models import ExpectedFile, UNIQUE_CONSTRAINT


KNOWN_FORMATS = {
    ".csv": {"reader": pandas.read_csv, "sep": ","},
    ".tsv": {"reader": pandas.read_csv, "sep": "\t"},
    ".txt": {"reader": pandas.read_csv, "sep": None},
}

logger = logging.getLogger(__name__)


def chunked_dataframe_reader(version, batch_size=None):
    """
    Read a tabular file into chunks of Dataframes and return a generator
    over those Dataframes
    """
    # Set proper storage backend based on settings
    version.set_storage()

    # Check file format
    _, ext = os.path.splitext(version.key.name)
    if ext not in KNOWN_FORMATS:
        raise IOError(
            "Unsupported file format. Unable to read "
            f"{version.pk} {version.file_name}"
        )

    # Read file into chunks (DataFrames)
    reader = KNOWN_FORMATS[ext]["reader"]
    delim = KNOWN_FORMATS[ext]["sep"]
    try:
        for i, chunk in enumerate(
            reader(version.key, sep=delim, chunksize=batch_size)
        ):
            yield chunk
    except Exception as e:
        logger.exception(
            f"Error in parsing {version.pk}: {version.file_name}"
            " content into a DataFrame."
        )
        raise


def batched_queryset_iterator(queryset, batch_size=None):
    """
    Yield lists of objects, with len batch_size, from a queryset iterator (
    e.g. Study.objects
    )
    """
    iterator = queryset.iterator(chunk_size=batch_size)
    for thing in iterator:
        yield [ti for ti in chain([thing], islice(iterator, batch_size - 1))]


def bulk_upsert_expected_files(files):
    """
    Bulk upsert ExpectedFile
    """
    with postgres_manager(ExpectedFile) as manager:
        return manager.bulk_upsert(UNIQUE_CONSTRAINT, rows=files)
