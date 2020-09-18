"""
This is an extract configuration for the `Participant Demographic and
Administrative File` template
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="Consent Short Name", out_col=CONCEPT.PARTICIPANT.CONSENT_TYPE
    ),
    keep_map(
        in_col="Administrative Gender", out_col=CONCEPT.PARTICIPANT.GENDER
    ),
    keep_map(in_col="Ethnicity", out_col=CONCEPT.PARTICIPANT.ETHNICITY),
    keep_map(
        in_col="Age at Study Enrollment",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Study Enrollment Units",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.UNITS,
    ),
    keep_map(
        in_col="Age at Last Contact",
        out_col=CONCEPT.PARTICIPANT.LAST_CONTACT.VALUE,
    ),
    keep_map(
        in_col="Age at Last Contact Units",
        out_col=CONCEPT.PARTICIPANT.LAST_CONTACT.UNITS,
    ),
]
