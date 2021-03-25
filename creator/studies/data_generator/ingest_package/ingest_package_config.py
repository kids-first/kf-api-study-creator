""" Ingest Package Config """

from kf_lib_data_ingest.common.concept_schema import CONCEPT

# The list of entities that will be loaded into the target service. These
# should be class_name values of your target API config's target entity
# classes.
target_service_entities = [
    "family",
    "participant",
    "biospecimen",
    "sequencing_experiment",
    "genomic_file",
    "biospecimen_genomic_file",
    "sequencing_experiment_genomic_file",
]

# All paths are relative to the directory this file is in
extract_config_dir = "extract_configs"

transform_function_path = "transform_module.py"

# Kids First Study ID
study = ""
