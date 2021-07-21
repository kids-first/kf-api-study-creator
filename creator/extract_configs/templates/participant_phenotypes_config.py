"""
This is an extract configuration for a Participant Phenotypes file.

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"


def map_hpo(v):
    """
    Map v to an HPO code
    """
    if v is None:
        return v
    else:
        return misc.map_hpo(str(v))


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
        optional=True,
    ),
    value_map(
        in_col="Condition HPO Code",
        m=map_hpo,
        out_col=CONCEPT.PHENOTYPE.HPO_ID,
        optional=True,
    ),

    # Not supported, by concept schema or Dataservice yet
    # keep_map(
    #     in_col="Verification Status",
    #     out_col=CONCEPT.PHENOTYPE.VERIFICATION
    # ),
    # keep_map(
    #     in_col="Body Site Name",
    #     out_col=CONCEPT.PHENOTYPE.ANATOMY_SITE.NAME,
    # ),
    # # UBERON
    # value_map(
    #     in_col="Body Site UBERON Code",
    #     m=misc.map_uberon,
    #     out_col=CONCEPT.PHENOTYPE.ANATOMY_SITE.UBERON_ID,
    # ),
    # keep_map(
    #     in_col="Age at Onset Value",
    #     out_col=CONCEPT.PHENOTYPE.EVENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Onset Units",
    #     out_col=CONCEPT.PHENOTYPE.EVENT_AGE.UNITS,
    # ),
    # keep_map(
    #     in_col="Age at Abatement Value",
    #     out_col=CONCEPT.PHENOTYPE.ABATEMENT_EVENT_AGE.VALUE,
    # ),
    # keep_map(
    #     in_col="Age at Abatement Units",
    #     out_col=CONCEPT.PHENOTYPE.ABATEMENT_EVENT_AGE.UNITS,
    # ),
]
