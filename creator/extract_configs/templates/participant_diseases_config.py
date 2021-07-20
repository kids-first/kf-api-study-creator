"""
This is an extract configuration for a Participant Diseases file.

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""

from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(in_col="Condition Name", out_col=CONCEPT.DIAGNOSIS.NAME),
    keep_map(
        in_col="Category",
        out_col=CONCEPT.DIAGNOSIS.CATEGORY,
    ),
    keep_map(
        in_col="Verification Status",
        out_col=CONCEPT.DIAGNOSIS.VERIFICATION,
        optional=True
    ),
    keep_map(
        in_col="Age at Onset Value",
        out_col=CONCEPT.DIAGNOSIS.EVENT_AGE.VALUE,
        optional=True
    ),
    keep_map(
        in_col="Age at Onset Units",
        out_col=CONCEPT.DIAGNOSIS.EVENT_AGE.UNITS,
        optional=True
    ),
    keep_map(
        in_col="Body Site Name",
        out_col=CONCEPT.DIAGNOSIS.TUMOR_LOCATION,
        optional=True
    ),
    value_map(
        in_col="Body Site UBERON Code",
        m=misc.map_uberon,
        out_col=CONCEPT.DIAGNOSIS.UBERON_TUMOR_LOCATION_ID,
        optional=True
    ),
    value_map(
        in_col="Condition MONDO Code",
        m=misc.map_mondo,
        out_col=CONCEPT.DIAGNOSIS.MONDO_ID,
        optional=True
    ),
    # Not supported, by concept schema or Dataservice yet
    # keep_map(
    #     in_col="Verification Status",
    #     out_col=CONCEPT.DIAGNOSIS.VERIFICATION
    # ),
    # keep_map(
    #     in_col="Age at Abatement Value",
    #     out_col=CONCEPT.DIAGNOSIS.ABATEMENT_EVENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Abatement Units",
    #     out_col=CONCEPT.DIAGNOSIS.ABATEMENT_EVENT_AGE.UNITS,
    # ),
    # keep_map(
    #     in_col="Body Site Name",
    #     out_col=CONCEPT.DIAGNOSIS.ANATOMY_SITE.NAME,
    # ),
    # # UBERON
    # value_map(
    #     in_col="Body Site UBERON Code",
    #     m=misc.map_uberon,
    #     out_col=CONCEPT.DIAGNOSIS.ANATOMY_SITE.UBERON_ID,
    # ),
]
