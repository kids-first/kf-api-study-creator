"""
This is an extract configuration for the Family Trios template
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(in_col="Participant ID", out_col=CONCEPT.PARTICIPANT.ID),
    keep_map(
        in_col="Mother Participant ID", out_col=CONCEPT.PARTICIPANT.MOTHER_ID
    ),
    keep_map(
        in_col="Father Participant ID", out_col=CONCEPT.PARTICIPANT.FATHER_ID
    ),
]
