"""
This is an extract configuration for a Complex Family file.

See: https://www.notion.so/d3b/Expedited-File-Types-and-Guidelines-fc5bd4390fa54de5a70b550d73779de9#9e9e1f8f66184484aa0a187e171365a7

Required Columns:
    Source Participant ID
    Target Participant ID
    Family Relationship
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(
        in_col="Source Participant ID",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.PERSON1.ID,
    ),
    keep_map(
        in_col="Target Participant ID",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.PERSON2.ID,
    ),
    keep_map(
        in_col="Family Relationship",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.RELATION_FROM_1_TO_2,
    ),
]
