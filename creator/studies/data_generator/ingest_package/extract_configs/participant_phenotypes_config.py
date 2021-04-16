"""
This is an extract configuration for a Participant Observations file.

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - phenotype
"""

from kf_lib_data_ingest.etl.extract.operations import keep_map
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from creator.extract_configs.templates.participant_phenotypes_config import (
    operations as shared_ops
)

source_data_url = "file://../data/bio_manifest.tsv"

operations = shared_ops + [
    keep_map(
        in_col="KF ID Participant",
        out_col=CONCEPT.PARTICIPANT.TARGET_SERVICE_ID,
    ),
]
