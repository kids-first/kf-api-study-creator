"""
Transform module to merge data generated by
creator.ingest_runs.data_generator.study_generator
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
    gf_df = merge_wo_duplicates(
        mapped_df_dict['s3_scrape_config.py'],
        mapped_df_dict['genomic.py'],
        on=CONCEPT.GENOMIC_FILE.ID,
    )
    df = merge_wo_duplicates(
        mapped_df_dict['biospec.py'],
        gf_df,
        on=CONCEPT.BIOSPECIMEN.ID,
    )

    return {DEFAULT_KEY: df}