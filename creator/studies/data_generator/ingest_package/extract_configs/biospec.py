"""
Extract config for bio manifest generated by
creator.ingest_runs.data_generator.study_generator

Contains minimal data needed to build Kids First Data Service entities:
- family
- participant
- biospecimen

See documentation at
https://kids-first.github.io/kf-lib-data-ingest/tutorial/extract.html for
information on writing extract config files.
"""

from kf_lib_data_ingest.common import constants  # noqa F401
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import *

source_data_url = "file://../data/bio_manifest.tsv"

source_data_read_params = {}

# (Optional) You can set a custom read function with
# source_data_read_func

operations = [
    keep_map(
        in_col="kf_id_family",
        out_col=CONCEPT.FAMILY.TARGET_SERVICE_ID,
    ),
    keep_map(
        in_col="family_id",
        out_col=CONCEPT.FAMILY.ID,
    ),
    keep_map(
        in_col="kf_id_participant",
        out_col=CONCEPT.PARTICIPANT.TARGET_SERVICE_ID,
    ),
    keep_map(
        in_col="participant_id",
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
    keep_map(
        in_col="kf_id_biospecimen",
        out_col=CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
    ),
    keep_map(
        in_col="sample_id",
        out_col=CONCEPT.BIOSPECIMEN.ID,
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
