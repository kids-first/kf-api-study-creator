"""
This is an extract configuration for a Sample Manifest

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - biospecimen
"""

from kf_lib_data_ingest.common import constants  # noqa F401
from kf_lib_data_ingest.etl.extract.operations import keep_map, constant_map
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from creator.extract_configs.templates.aliquot_manifest_config import operations as shared_ops  # noqa

source_data_url = "file://../data/bio_manifest.tsv"

operations = shared_ops + [
    constant_map(
        m=constants.SEQUENCING.CENTER.BROAD.KF_ID,
        out_col=CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
    ),
]
