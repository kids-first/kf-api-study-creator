"""
This is an extract configuration for the Family Trios template

See: https://www.notion.so/d3b/Expedited-File-Types-and-Guidelines-fc5bd4390fa54de5a70b550d73779de9#9e9e1f8f66184484aa0a187e171365a7

Required Columns:
    Participant ID
    Mother Participant ID
    Father Participant ID
    Proband
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
    keep_map(
        in_col="Proband",
        out_col=CONCEPT.PARTICIPANT.IS_PROBAND,
        optional=True
    ),
]
