"""
This is an extract configuration for a Complex Family file.

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"


operations = [
    keep_map(
        in_col="First Participant ID",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.PERSON1.ID,
    ),
    keep_map(
        in_col="Second Participant ID",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.PERSON2.ID,
    ),
    keep_map(
        in_col="Relationship from First to Second",
        out_col=CONCEPT.FAMILY_RELATIONSHIP.RELATION_FROM_1_TO_2,
    ),
]
