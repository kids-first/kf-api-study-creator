"""
This is an extract configuration for a Sample Manifest

See: https://www.notion.so/d3b/Internal-File-Types-and-Guidelines-6edd92087f04445e84a236202831edbd#aa2c7d8a50164a08ab685b42b784293e

Required Columns:
    Participant ID
    Sample ID
    Aliquot ID
    Consent Group
    Tissue Type
    Composition
    Body Site Name
    Body Site UBERON Code
    Age at Collection Value
    Age at Collection Units
    Descriptor
    Method of Sample Procurement
    Volume
    Volume Units
    Concentration
    Concentration Units
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"

operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(in_col="Sample ID", out_col=CONCEPT.BIOSPECIMEN_GROUP.ID),
    keep_map(
        in_col="Consent Group",
        out_col=CONCEPT.BIOSPECIMEN.DBGAP_STYLE_CONSENT_CODE
    ),
    keep_map(
        in_col="Consent Short Name",
        out_col=CONCEPT.BIOSPECIMEN.CONSENT_SHORT_NAME
    ),
    keep_map(
        in_col="Aliquot ID", out_col=CONCEPT.BIOSPECIMEN.ID
    ),
    keep_map(
        in_col="Tissue Type",
        out_col=CONCEPT.BIOSPECIMEN.TISSUE_TYPE,
    ),
    keep_map(
        in_col="Composition",
        out_col=CONCEPT.BIOSPECIMEN.COMPOSITION,
    ),
    keep_map(
        in_col="Body Site Name",
        out_col=CONCEPT.BIOSPECIMEN.ANATOMY_SITE,
    ),
    value_map(
        in_col="Body Site UBERON Code",
        m=misc.map_uberon,
        out_col=CONCEPT.BIOSPECIMEN.UBERON_ANATOMY_SITE_ID,
    ),
    keep_map(
        in_col="Age at Collection Value",
        out_col=CONCEPT.BIOSPECIMEN.EVENT_AGE_DAYS,
    ),
    keep_map(
        in_col="Descriptor",
        out_col=CONCEPT.BIOSPECIMEN.TUMOR_DESCRIPTOR,
    ),
    keep_map(
        in_col="Descriptor",
        out_col=CONCEPT.BIOSPECIMEN.SPATIAL_DESCRIPTOR,
    ),
    keep_map(
        in_col="Method of Sample Procurement",
        out_col=CONCEPT.BIOSPECIMEN.SAMPLE_PROCUREMENT,
    ),
    keep_map(
        in_col="Volume",
        out_col=CONCEPT.BIOSPECIMEN.VOLUME_UL,
    ),
    keep_map(
        in_col="Concentration",
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION_MG_PER_ML,
    ),
    # Not supported by target service yet but still good to include
    # so that we can capture the data for the future
    keep_map(
        in_col="Age at Collection Value",
        out_col=CONCEPT.BIOSPECIMEN.EVENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Collection Units",
        out_col=CONCEPT.BIOSPECIMEN.EVENT_AGE.UNITS,
    ),
    keep_map(
        in_col="Volume",
        out_col=CONCEPT.BIOSPECIMEN.VOLUME.VALUE,
    ),
    keep_map(
        in_col="Volume Units",
        out_col=CONCEPT.BIOSPECIMEN.VOLUME.UNITS,
    ),
    keep_map(
        in_col="Concentration",
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.VALUE,
    ),
    keep_map(
        in_col="Concentration Units",
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.UNITS,
    ),
]
