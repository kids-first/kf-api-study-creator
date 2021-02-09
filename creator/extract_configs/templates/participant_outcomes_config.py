"""
This is an extract configuration for the `Participant Outcomes File` template

See: https://www.notion.so/d3b/Internal-File-Types-and-Guidelines-6edd92087f04445e84a236202831edbd#aa2c7d8a50164a08ab685b42b784293e

Required Columns:
    Participant ID
    Vital Status
    Age at Status Value
    Age at Status Units
    Disease Related
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="Vital Status",
        out_col=CONCEPT.OUTCOME.VITAL_STATUS,
    ),
    keep_map(
        in_col="Disease Related",
        out_col=CONCEPT.OUTCOME.DISEASE_RELATED,
    ),
    keep_map(
        in_col="Age at Status Value",
        out_col=CONCEPT.OUTCOME.EVENT_AGE_DAYS,
    ),

    # Not supported by target service yet but still good to include
    # so that we can capture the data for the future
    keep_map(
        in_col="Age at Status Value",
        out_col=CONCEPT.OUTCOME.EVENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Status Units",
        out_col=CONCEPT.OUTCOME.EVENT_AGE.UNITS,
    ),
]
