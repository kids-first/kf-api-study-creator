"""
Auto-generated extract config module.

See documentation at
https://kids-first.github.io/kf-lib-data-ingest/tutorial/extract.html for
information on writing extract config files.
"""
import os
from kf_lib_data_ingest.common import constants, pandas_utils  # noqa F401
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import *
from kf_lib_data_ingest.common.io import read_df

DATA_DIR = (
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data"
    )
)
source_data_url = "file://../data/gf_manifest.tsv"


# TODO (Optional) Fill in special loading parameters here
source_data_read_params = {}

# TODO (Optional) You can set a custom read function with
# source_data_read_func


# TODO - Replace this with operations that make sense for your own data file
operations = [
    keep_map(
        in_col="project_id",
        out_col=CONCEPT.SEQUENCING.ID,
    ),
    keep_map(
        in_col="sample_id",
        out_col=CONCEPT.BIOSPECIMEN.ID,
    ),
    constant_map(
        out_col=CONCEPT.SEQUENCING.STRATEGY,
        m=constants.SEQUENCING.STRATEGY.WGS,
    ),
    # Source genomic file KF ID
    keep_map(
        in_col="kf_id_genomic_file",
        out_col=CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
    ),
    keep_map(
        in_col="source_read",
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
