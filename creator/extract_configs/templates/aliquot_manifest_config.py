"""
This is an extract configuration for a Aliquot Manifest

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map, value_map
from kf_lib_data_ingest.common import misc

source_data_url = "{{ download_url }}"

operations = [
    keep_map(in_col="Specimen ID", out_col=CONCEPT.BIOSPECIMEN_GROUP.ID),
    keep_map(
        in_col="Aliquot ID", out_col=CONCEPT.BIOSPECIMEN.ID
    ),
    keep_map(
        in_col="Analyte Type",
        out_col=CONCEPT.BIOSPECIMEN.ANALYTE,
    ),
    keep_map(
        in_col="Sequencing Center",
        out_col=CONCEPT.SEQUENCING.CENTER.NAME,
    ),
]
