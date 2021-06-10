"""
This is an extract configuration for a Biospecimen Collection Manifest

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"

operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(in_col="Specimen ID", out_col=CONCEPT.BIOSPECIMEN_GROUP.ID),
    keep_map(
        in_col="Consent Group",
        out_col=CONCEPT.BIOSPECIMEN.DBGAP_STYLE_CONSENT_CODE
    ),
    keep_map(
        in_col="Consent Short Name",
        out_col=CONCEPT.BIOSPECIMEN.CONSENT_SHORT_NAME
    ),
    keep_map(
        in_col="Tissue Type Name",
        out_col=CONCEPT.BIOSPECIMEN.TISSUE_TYPE,
    ),
    keep_map(
        in_col="Composition Name",
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
        in_col="Method of Sample Procurement",
        out_col=CONCEPT.BIOSPECIMEN.SAMPLE_PROCUREMENT,
    ),
    keep_map(
        in_col="Quantity Value",
        out_col=CONCEPT.BIOSPECIMEN.VOLUME_UL,
    ),
    keep_map(
        in_col="Concentration Value",
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION_MG_PER_ML,
    ),
    # Not supported, by concept schema or Dataservice yet
    # keep_map(
    #     in_col="Age at Collection Value",
    #     out_col=CONCEPT.BIOSPECIMEN.EVENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Collection Units",
    #     out_col=CONCEPT.BIOSPECIMEN.EVENT_AGE.UNITS,
    # ),
    # keep_map(
    #     in_col="Volume",
    #     out_col=CONCEPT.BIOSPECIMEN.VOLUME.VALUE,
    # ),
    # keep_map(
    #     in_col="Volume Units",
    #     out_col=CONCEPT.BIOSPECIMEN.VOLUME.UNITS,
    # ),
    # keep_map(
    #     in_col="Concentration",
    #     out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.VALUE,
    # ),
    # keep_map(
    #     in_col="Concentration Units",
    #     out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.UNITS,
    # ),
]
