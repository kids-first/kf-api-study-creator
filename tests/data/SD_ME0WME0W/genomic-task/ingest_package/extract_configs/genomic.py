"""
Auto-generated extract config module.

See documentation at
https://kids-first.github.io/kf-lib-data-ingest/tutorial/extract.html for
information on writing extract config files.
"""
import pandas as pd

from kf_lib_data_ingest.common import constants  # noqa F401
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import *

# TODO - Replace this with a URL to your own data file
source_data_url = "file://../../data/gen_manifest.csv"

def do_after_read(df):
    s3_scrape = pd.read_csv("data/s3_scrape.csv")
    merged_df = df.merge(
        right=s3_scrape,
        left_on="filepath",
        right_on="Filepath",
        how="inner"
    )
    return merged_df

# TODO (Optional) Fill in special loading parameters here
source_data_read_params = {}

# TODO (Optional) You can set a custom read function with
# source_data_read_func


# TODO - Replace this with operations that make sense for your own data file
operations = [
    value_map(
        in_col="project_id",
        m={r"RP-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.SEQUENCING.ID,
    ),
    value_map(
        in_col="biospec_id",
        m={r"SM-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.BIOSPECIMEN.ID,
    ),
    constant_map(
        out_col=CONCEPT.SEQUENCING.STRATEGY,
        m=constants.SEQUENCING.STRATEGY.WGS,
    ),
    value_map(
        in_col="participant_id",
        m={r"CARE-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.PARTICIPANT.ID,
    ),
    value_map(
        in_col="filepath",
        m=lambda x: [str(x)],
        out_col=CONCEPT.GENOMIC_FILE.URL_LIST,
    ),
    value_map(
        in_col="ETag",
        m=lambda x: {constants.FILE.HASH.S3_ETAG: str(x)},
        out_col=CONCEPT.GENOMIC_FILE.HASH_DICT,
    ),
    value_map(
        in_col="Size",
        m=lambda x: float(x),
        out_col=CONCEPT.GENOMIC_FILE.SIZE,
    ),
    keep_map(
        in_col="Filename",
        out_col=CONCEPT.GENOMIC_FILE.FILE_NAME,
    ),
    keep_map(
        in_col="filepath",
        out_col=CONCEPT.GENOMIC_FILE.ID,
    ),
    constant_map(
        m=False,
        out_col=CONCEPT.GENOMIC_FILE.HARMONIZED,
    ),
    constant_map(
        m=constants.SEQUENCING.REFERENCE_GENOME.GRCH38,
        out_col=CONCEPT.GENOMIC_FILE.REFERENCE_GENOME,
    ),
    constant_map(
        m=True,
        out_col=CONCEPT.SEQUENCING.PAIRED_END,
    ),
]
