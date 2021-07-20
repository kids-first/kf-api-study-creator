"""
This is an extract configuration for the Participant Details file

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, row_map

source_data_url = "{{ download_url }}"


def disease_related(row):
    """
    Determine whether the cause of death was disease related or not from
    the value for Last Known Vital Status
    """
    last_vital = row.get("Last Known Vital Status", "Unknown") or "Unknown"

    if "deceased by disease" in last_vital.lower():
        ret = True
    elif "unknown" in last_vital.lower():
        ret = False
    else:
        ret = None

    return ret


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="Clinical Sex", out_col=CONCEPT.PARTICIPANT.GENDER
    ),
    keep_map(
        in_col="Affected Status",
        out_col=CONCEPT.PARTICIPANT.IS_AFFECTED_UNDER_STUDY,
    ),
    keep_map(
        in_col="Proband",
        out_col=CONCEPT.PARTICIPANT.IS_PROBAND,
    ),
    keep_map(
        in_col="Family ID",
        out_col=CONCEPT.FAMILY.ID,
        optional=True,
    ),
    keep_map(
        in_col="Last Known Vital Status",
        out_col=CONCEPT.OUTCOME.VITAL_STATUS,
        optional=True,
    ),
    row_map(
        m=disease_related,
        out_col=CONCEPT.OUTCOME.DISEASE_RELATED,
    ),
    keep_map(
        in_col="dbGaP Consent Code",
        out_col=CONCEPT.PARTICIPANT.CONSENT_TYPE,
        optional=True,
    ),
    keep_map(
        in_col="Age at Study Enrollment Value",
        out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE_DAYS,
        optional=True,
    ),
    keep_map(
        in_col="Race",
        out_col=CONCEPT.PARTICIPANT.RACE,
        optional=True,
    ),
    keep_map(
        in_col="Ethnicity",
        out_col=CONCEPT.PARTICIPANT.ETHNICITY,
        optional=True,
    ),
    keep_map(
        in_col="Species",
        out_col=CONCEPT.PARTICIPANT.SPECIES,
        optional=True,
    ),

    # Not supported by concept schema or Dataservice yet
    # keep_map(
    #     in_col="Gender Identity", out_col=CONCEPT.PARTICIPANT.GENDER_IDENTITY
    # ),
    # keep_map(
    #     in_col="Clinical Sex", out_col=CONCEPT.PARTICIPANT.SEX
    # ),
    # keep_map(
    #     in_col="Age at Study Enrollment Value",
    #     out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Study Enrollment Units",
    #     out_col=CONCEPT.PARTICIPANT.ENROLLMENT_AGE.UNITS,
    # ),
    # keep_map(
    #     in_col="Age at Status Value",
    #     out_col=CONCEPT.OUTCOME.EVENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Status Units",
    #     out_col=CONCEPT.OUTCOME.EVENT_AGE.UNITS,
    # ),
]
