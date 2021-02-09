"""
This is an extract configuration for a Participant Observations file.

See: https://www.notion.so/d3b/a7c4a98cab854d05aaf3e8e73469ac57?v=b5ee7a0282084f25b6b0a2a925e1bec6

Required Columns:
    Participant ID
    Observation Ontology Ontobee URI
    Observation Name
    Observation Code
    Status
    Category
    Interpretation
    Age at Observation Value
    Age at Observation Units
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(in_col="Status", out_col=CONCEPT.OBSERVATION.STATUS),
    keep_map(in_col="Category", out_col=CONCEPT.OBSERVATION.CATEGORY),
    keep_map(
        in_col="Interpretation",
        out_col=CONCEPT.OBSERVATION.INTERPRETATION,
        optional=True,
    ),
    keep_map(in_col="Observation Name", out_col=CONCEPT.OBSERVATION.NAME),
    keep_map(in_col="Observation Ontology Ontobee URI",
             out_col=CONCEPT.OBSERVATION.ONTOLOGY_ONTOBEE_URI),
    # SNOMEDCT
    value_map(
        in_col="Observation Code",
        m=misc.map_snomed,
        out_col=CONCEPT.OBSERVATION.SNOMED_ID,
        optional=True,
    ),
    # HPO
    value_map(
        in_col="Observation Code",
        m=misc.map_hpo,
        out_col=CONCEPT.OBSERVATION.HPO_ID,
        optional=True,
    ),
    # NCIT
    value_map(
        in_col="Observation Code",
        m=misc.map_ncit,
        out_col=CONCEPT.OBSERVATION.NCIT_ID,
        optional=True,
    ),
    # MONDO
    value_map(
        in_col="Observation Code",
        m=misc.map_mondo,
        out_col=CONCEPT.OBSERVATION.MONDO_ID,
        optional=True,
    ),
    keep_map(
        in_col="Age at Observation Value",
        out_col=CONCEPT.OBSERVATION.EVENT_AGE.VALUE,
        optional=True,
    ),
    keep_map(
        in_col="Age at Observation Units",
        out_col=CONCEPT.OBSERVATION.EVENT_AGE.UNITS,
        optional=True,
    ),
]
