"""
This is an extract configuration for a Complex Family file.

Operations are inherited from the standard Study Creator extract configs in
creator/extract_configs/templates

The Dataservice entities that will be built from this are:
    - family_relationship
"""
from creator.extract_configs.templates.complex_family_config import operations

source_data_url = "file://../data/bio_manifest.tsv"
