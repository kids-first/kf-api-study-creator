"""
This is an extract config intended for Genomic Workflow Output Manifests
produced by the Bix team.

See: https://www.notion.so/d3b/Expedited-File-Types-and-Guidelines-fc5bd4390fa54de5a70b550d73779de9#9e9e1f8f66184484aa0a187e171365a7

Required Columns:
    Cavatica ID
    Cavatica Task ID
    KF Biospecimen ID
    KF Participant ID
    KF Family ID
    Filepath
    Data Type
    Workflow Type
    Source Read
"""

from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map, value_map, Split
)

source_data_url = "{{ download_url }}"

operations = [
    keep_map(
        in_col="Data Type",
        out_col=CONCEPT.GENOMIC_FILE.DATA_TYPE,
    ),
    keep_map(
        in_col="Filepath",
        out_col=CONCEPT.GENOMIC_FILE.ID,
    ),
    value_map(
        in_col="KF Biospecimen ID",
        m=lambda x: Split(x.split(",")),
        out_col=CONCEPT.BIOSPECIMEN.ID,
    ),
]
