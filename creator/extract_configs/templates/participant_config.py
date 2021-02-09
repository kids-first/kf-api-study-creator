"""
This is an extract configuration for the `Participant Demographic and
Administrative File` template

See: https://www.notion.so/d3b/Internal-File-Types-and-Guidelines-6edd92087f04445e84a236202831edbd#aa2c7d8a50164a08ab685b42b784293e

Required Columns:
    Family ID
    Participant ID
    dbGaP Consent Code
    Affected Status
    Gender Identity
    Clinical Sex
    Race
    Ethnicity
    Species
    Age at Study Enrollment Value
    Age at Study Enrollment Units
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Family ID", out_col=CONCEPT.FAMILY.ID),
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="dbGaP Consent Code", out_col=CONCEPT.PARTICIPANT.CONSENT_TYPE
    ),
    keep_map(
        in_col="Affected Status",
        out_col=CONCEPT.PARTICIPANT.IS_AFFECTED_UNDER_STUDY,
    ),
    keep_map(
        in_col="Clinical Sex", out_col=CONCEPT.PARTICIPANT.GENDER
    ),
    keep_map(
        in_col="Age at Study Enrollment Value",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE_DAYS,
    ),
    keep_map(in_col="Race", out_col=CONCEPT.PARTICIPANT.RACE),
    keep_map(in_col="Ethnicity", out_col=CONCEPT.PARTICIPANT.ETHNICITY),
    keep_map(in_col="Species", out_col=CONCEPT.PARTICIPANT.SPECIES),

    # Not supported by target service yet but still good to include
    # so that we can capture the data for the future
    keep_map(
        in_col="Gender Identity", out_col=CONCEPT.PARTICIPANT.GENDER_IDENTITY
    ),
    keep_map(
        in_col="Clinical Sex", out_col=CONCEPT.PARTICIPANT.SEX
    ),
    keep_map(
        in_col="Age at Study Enrollment Value",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.VALUE,
    ),
    keep_map(
        in_col="Age at Study Enrollment Units",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.UNITS,
    ),
]
