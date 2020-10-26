"""
This is an extract config intended for Genomic Workflow Output Manifests
produced by the Bix team. This manifest contains the list of files produced
by the genomic harmonization workflows along with the attached specimens,
and source genomic files.

To use this extract config, you can make a copy of it and add it to your
ingest package or you can import it as a module in an existing extract config
and override at least the `source_data_url`. You may also append additional:w

operations to the `operations` list as well.
"""

from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map, value_map, Split
)

source_data_url = "{{ download_url }}"

operations = [
    keep_map(
        in_col="data_type",
        out_col=CONCEPT.GENOMIC_FILE.DATA_TYPE,
    ),
    keep_map(
        in_col="filepath",
        out_col=CONCEPT.GENOMIC_FILE.ID,
    ),
    value_map(
        in_col="kf_biospecimen_id",
        m=lambda x: Split(x.split(",")),
        out_col=CONCEPT.BIOSPECIMEN.ID,
    ),
]
