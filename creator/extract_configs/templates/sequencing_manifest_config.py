"""
This is an extract configuration for a Sequencing File Manifest template

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map,
    constant_map,
    row_map
)

source_data_url = "{{ download_url }}"


def file_hash(row):
    """
    Return a dict with the sequencing file's hashes keyed by hash algorithm
    """
    hash_algo = row.get("File Hash Algorithm", "Unknown") or "Unknown"
    return {
        hash_algo: row.get("Sequencing Output File Hash")
    }


operations = [
    keep_map(
        in_col="Aliquot ID", out_col=CONCEPT.BIOSPECIMEN.ID
    ),
    keep_map(
        in_col="Sequencing Center",
        out_col=CONCEPT.SEQUENCING.CENTER.NAME,
    ),
    keep_map(
        in_col="Sequencing Output Filepath",
        out_col=CONCEPT.GENOMIC_FILE.ID,
    ),
    keep_map(
        in_col="Reference Genome",
        out_col=CONCEPT.GENOMIC_FILE.REFERENCE_GENOME,
    ),
    keep_map(
        in_col="Sequencing Library Name",
        out_col=CONCEPT.SEQUENCING.ID,
    ),
    keep_map(
        in_col="Sequencing Library Name",
        out_col=CONCEPT.SEQUENCING.LIBRARY_NAME,
    ),
    keep_map(
        in_col="Experiment Strategy",
        out_col=CONCEPT.SEQUENCING.STRATEGY,
    ),
    keep_map(
        in_col="Sequencing Platform",
        out_col=CONCEPT.SEQUENCING.PLATFORM,
    ),
    keep_map(
        in_col="Is Paired End",
        out_col=CONCEPT.SEQUENCING.PAIRED_END,
    ),
    row_map(
        out_col=CONCEPT.GENOMIC_FILE.HASH_DICT,
        m=file_hash
    ),
    keep_map(
        in_col="Experiment Date",
        out_col=CONCEPT.SEQUENCING.DATE,
        optional=True,
    ),
    keep_map(
        in_col="Instrument Model",
        out_col=CONCEPT.SEQUENCING.INSTRUMENT,
        optional=True,
    ),
    keep_map(
        in_col="Library Strand",
        out_col=CONCEPT.SEQUENCING.LIBRARY_STRAND,
        optional=True,
    ),
    keep_map(
        in_col="Library Selection",
        out_col=CONCEPT.SEQUENCING.LIBRARY_SELECTION,
        optional=True,
    ),
    keep_map(
        in_col="Library Prep Kit",
        out_col=CONCEPT.SEQUENCING.LIBRARY_PREP,
        optional=True,
    ),
    keep_map(
        in_col="Expected Mean Insert Size",
        out_col=CONCEPT.SEQUENCING.MEAN_INSERT_SIZE,
        optional=True,
    ),
    keep_map(
        in_col="Expected Mean Depth",
        out_col=CONCEPT.SEQUENCING.MEAN_DEPTH,
        optional=True,
    ),
    keep_map(
        in_col="Expected Mean Read Length",
        out_col=CONCEPT.SEQUENCING.MEAN_READ_LENGTH,
        optional=True,
    ),
    keep_map(
        in_col="Expected Total Reads",
        out_col=CONCEPT.SEQUENCING.TOTAL_READS,
        optional=True,
    ),
    constant_map(
        m=False,
        out_col=CONCEPT.GENOMIC_FILE.HARMONIZED,
    ),
]
