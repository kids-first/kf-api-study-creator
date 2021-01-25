"""
Auto-generated extract config module.

See documentation at
https://kids-first.github.io/kf-lib-data-ingest/tutorial/extract.html for
information on writing extract config files.
"""

from kf_lib_data_ingest.common import constants  # noqa F401
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import *

# TODO - Replace this with a URL to your own data file
source_data_url = "file://../../data/bio_manifest.csv" # noqa

# TODO (Optional) Fill in special loading parameters here
source_data_read_params = {}

# TODO (Optional) You can set a custom read function with
# source_data_read_func


# TODO - Replace this with operations that make sense for your own data file
operations = [
    value_map(
        in_col="sample_id",
        m={r"SM-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.BIOSPECIMEN.ID,
    ),
    value_map(
        in_col="participant_id",
        m={r"CARE-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.PARTICIPANT.ID,
    ),
    value_map(
        in_col="gender",
        m={
            "Male": constants.GENDER.MALE,
            "Female": constants.GENDER.FEMALE,
        },
        out_col=CONCEPT.PARTICIPANT.GENDER,
    ),
    value_map(
        in_col="volume",
        m=lambda x: float(x),
        out_col=CONCEPT.BIOSPECIMEN.VOLUME_UL,
    ),
    value_map(
        in_col="concentration",
        m=lambda x: float(x),
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION_MG_PER_ML,
    ),
    value_map(
        in_col="family_id",
        m={r"FA-(\d+)": lambda x: int(x)},
        out_col=CONCEPT.FAMILY.ID,
    ),
    keep_map(
        in_col="tissue_type",
        out_col=CONCEPT.BIOSPECIMEN.TISSUE_TYPE,
    ),
    constant_map(
        m=constants.SEQUENCING.CENTER.BROAD.KF_ID,
        out_col=CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
    ),
    constant_map(
        m=constants.SEQUENCING.ANALYTE.DNA,
        out_col=CONCEPT.BIOSPECIMEN.ANALYTE,
    ),
]
