"""
This is an extract configuration for a Sequencing Manifest

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - sequencing_experiment
"""
from kf_lib_data_ingest.common import constants  # noqa F401
from kf_lib_data_ingest.etl.extract.operations import keep_map, constant_map
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from creator.extract_configs.templates.sequencing_manifest_config import (
    operations as shared_ops
)

source_data_url = "file://../data/sequencing_manifest.tsv"

operations = shared_ops + [
    constant_map(
        m=constants.SEQUENCING.CENTER.BROAD.KF_ID,
        out_col=CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
    ),
    keep_map(
        in_col="KF ID Source Genomic File",
        out_col=CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
    ),
]
