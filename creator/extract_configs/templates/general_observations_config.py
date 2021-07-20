"""
This is an extract configuration for a General Observations file.

**NOTE**
Not currently supported by Dataservice, but keep this extract config
so we can capture things that don't fit into the data model as
general observations

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(in_col="Observation Name", out_col=CONCEPT.OBSERVATION.NAME),
    keep_map(in_col="Category", out_col=CONCEPT.OBSERVATION.CATEGORY),
    keep_map(in_col="Status", out_col=CONCEPT.OBSERVATION.STATUS),
    keep_map(
        in_col="Interpretation",
        out_col=CONCEPT.OBSERVATION.INTERPRETATION,
        optional=True,
    ),
    keep_map(
        in_col="Observation Ontology Ontobee URI",
        out_col=CONCEPT.OBSERVATION.ONTOLOGY_ONTOBEE_URI,
        optional=True,
    ),
    keep_map(
        in_col="Observation Code",
        out_col=CONCEPT.OBSERVATION.ONTOLOGY_CODE,
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
