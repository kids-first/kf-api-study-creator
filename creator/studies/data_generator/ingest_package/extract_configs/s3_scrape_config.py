"""
This is an extract configuration for S3 object manifests.

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - genomic_file
"""

from creator.extract_configs.templates.s3_scrape_config import *

source_data_url = "file://../data/s3_source_gf_manifest.tsv"
