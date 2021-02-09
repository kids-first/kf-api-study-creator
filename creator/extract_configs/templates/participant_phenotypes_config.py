"""
This is an extract configuration for a Participant Phenotypes file.

See: https://www.notion.so/d3b/21e80815ba654a5fbc25f5a17b9e67a4?v=e8e02f33f87f47ff912350224cd5ab0f

Required Columns:
    Participant ID
    Condition Name
    Condition HPO Code
    Body Site Name
    Body Site UBERON Code
    Verification Status
    Age at Onset Value
    Age at Onset Units
    Age at Abatement Value
    Age at Abatement Units
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="Verification Status",
        out_col=CONCEPT.PHENOTYPE.OBSERVED
    ),
    keep_map(in_col="Condition Name", out_col=CONCEPT.PHENOTYPE.NAME),
    keep_map(
        in_col="Age at Onset Value",
        out_col=CONCEPT.PHENOTYPE.EVENT_AGE_DAYS,
    ),
    value_map(
        in_col="Condition HPO Code",
        m=misc.map_hpo,
        out_col=CONCEPT.PHENOTYPE.HPO_ID,
    ),

    # Not supported by target service yet but still good to include
    # so that we can capture the data for the future
    keep_map(
        in_col="Verification Status",
        out_col=CONCEPT.PHENOTYPE.VERIFICATION
    ),
    keep_map(
        in_col="Body Site Name",
        out_col=CONCEPT.PHENOTYPE.ANATOMY_SITE.NAME,
    ),
    # UBERON
    value_map(
        in_col="Body Site UBERON Code",
        m=misc.map_uberon,
        out_col=CONCEPT.PHENOTYPE.ANATOMY_SITE.UBERON_ID,
    ),
    keep_map(
        in_col="Age at Onset Value",
        out_col=CONCEPT.PHENOTYPE.EVENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Onset Units",
        out_col=CONCEPT.PHENOTYPE.EVENT_AGE.UNITS,
    ),
    keep_map(
        in_col="Age at Abatement Value",
        out_col=CONCEPT.PHENOTYPE.ABATEMENT_EVENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Abatement Units",
        out_col=CONCEPT.PHENOTYPE.ABATEMENT_EVENT_AGE.UNITS,
    ),
]
