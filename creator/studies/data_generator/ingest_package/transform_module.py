"""
Transform module to merge data generated by
creator.ingest_runs.data_generator.study_generator

This will generate the following Kids First Dataservice entities:
    family
    participant
    biospecimen
    diagnosis
    phenotype
    outcome
    sequencing_experiment
    genomic_file
    biospecimen_genomic_file
    sequencing_experiment_genomic_file
"""

from kf_lib_data_ingest.common.concept_schema import CONCEPT  # noqa F401

# Use these merge funcs, not pandas.merge
from kf_lib_data_ingest.common.pandas_utils import (  # noqa F401
    merge_wo_duplicates,
    outer_merge,
)
from kf_lib_data_ingest.config import DEFAULT_KEY


def transform_function(mapped_df_dict):
    """
    Merge clinical and genomic data together
    """
    # Merge clinical data together
    df = merge_wo_duplicates(
        mapped_df_dict['family_trio_config.py'],
        mapped_df_dict['participant_config.py'],
        on=CONCEPT.PARTICIPANT.ID,
    )
    df = merge_wo_duplicates(
        df,
        mapped_df_dict['participant_diseases_config.py'],
        on=CONCEPT.PARTICIPANT.ID,
    )
    df = merge_wo_duplicates(
        df,
        mapped_df_dict['participant_phenotypes_config.py'],
        on=CONCEPT.PARTICIPANT.ID,
    )
    df = merge_wo_duplicates(
        df,
        mapped_df_dict['participant_outcomes_config.py'],
        on=CONCEPT.PARTICIPANT.ID,
    )
    bio_df = merge_wo_duplicates(
        df,
        mapped_df_dict['sample_manifest_config.py'],
        on=CONCEPT.PARTICIPANT.ID,
    )
    # Merge genomic data together
    gf_df = merge_wo_duplicates(
        mapped_df_dict['s3_scrape_config.py'],
        mapped_df_dict['sequencing_manifest_config.py'],
        on=CONCEPT.GENOMIC_FILE.ID,
    )
    # Merge clinical and genomic data
    df = merge_wo_duplicates(
        bio_df,
        gf_df,
        on=CONCEPT.BIOSPECIMEN.ID,
    )

    return {DEFAULT_KEY: df}
