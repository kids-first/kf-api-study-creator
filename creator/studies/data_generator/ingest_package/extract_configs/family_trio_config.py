"""
This is an extract configuration for the Family Trios template

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - family
    - family_relationship
"""

from kf_lib_data_ingest.etl.extract.operations import keep_map
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from creator.extract_configs.templates.family_trio_config import (
    operations as shared_ops
)

source_data_url = "file://../data/bio_manifest.tsv"

operations = shared_ops + [
    keep_map(
        in_col="KF ID Family",
        out_col=CONCEPT.FAMILY.TARGET_SERVICE_ID,
    ),
]
