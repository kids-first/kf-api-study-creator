import boto3
import pandas as pd
import os

from d3b_utils.aws_bucket_contents import fetch_bucket_obj_info
from kf_lib_data_ingest.app import settings
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.etl.load.load import LoadStage
from kf_utils.dataservice.scrape import yield_entities

from urllib.parse import urlparse

DATASERVICE_URL = "https://kf-api-dataservice.kidsfirstdrc.org/"
GENOMIC_FILES = "genomic-files"
SEQUENCING_EXPERIMENTS = "sequencing-experiments"
SEQUENCING_EXPERIMENT_GENOMIC_FILES = "sequencing-experiment-genomic-files"
BIOSPECIMEN_GENOMIC_FILES = "biospecimen-genomic-files"


def ingest_manifest(version):
    """
    Performs the full ingest process for a genomic workflow manifest _version_.
    """
    # Need to use _extract_data_ method on Version, but not sure exactly how
    # this works. It doesn't work with any of the Versions in the django shell.
    # How was it tested?

    # get_metadata(manifest_df)
    pass


def get_metadata(manifest_df):
    """
    Scrape the metadata for each file in the manifest from S3, put it into a
    DataFrame, join this with _manifest_df_ on Filepath, and return it.
    """
    assert not manifest_df.empty, "Empty manifest DataFrame"
    assert "Filepath" in manifest_df.columns, "Missing Filepath column"

    buckets = set()
    for row in manifest_df["Filepath"]:
        bucket, _ = os.path.split(row)
        buckets.add(bucket)

    # For each path, get metadata about files therein
    file_dicts = []
    for bucket in buckets:
        parsed_s3 = urlparse(bucket)

        file_dicts.extend(
            fetch_bucket_obj_info(
                parsed_s3.netloc,
                search_prefixes=parsed_s3.path,
            )
        )
    file_df = pd.DataFrame(file_dicts)

    # Inner join between the manifest DataFrame and our S3 metadata DataFrame
    # on the Filepath key.
    genomic_df = manifest_df.merge(right=file_df, on="Filepath", how="inner")

    return genomic_df


def load_harmonized_genomic_files(genomic_df, study_id):
    """
    Load data for the harmonized genomic files found in the manifest into the
    DataService (this data is in _genomic_df_).
    This step must occur before the others so that we can use the
    kf_ids created here for the rest of the process. After ingestion, query
    DataService for the newly-created kf_ids, add them to _genomic_df_,
    and return the DataFrame.
    """
    genomic_df = munge_genomic_df(genomic_df)
    load_entities(
        'genomic_file',
        #genomic_df.drop('CONCEPT.BIOSPECIMEN.ID', axis=1),
        pd.DataFrame(),
        study_id
    )


def load_entities(entity_type, df, study_id):
    """
    Load data of type _entity_type_ into the DataService from _df_.
    """
    target_service_base_url = "https://localhost:5000"
    app_settings = settings.load()
    loader = LoadStage(
        app_settings.TARGET_API_CONFIG,
        target_service_base_url,
        [entity_type],
        study_id,
        cache_dir=os.getcwd(),
    )
    loader.run({entity_type: df})


def munge_genomic_df(df):
    """
    Clean up _df_ and get it ready to be ingested.
    """
    print(df.columns)
    df['Hashes'] = df.apply(lambda row: {"ETag": row['ETag']}, axis=1)
    df['urls'] = df.apply(lambda row: [row['Filepath']], axis=1)
    col_rename = {
        'KF Biospecimen ID': 'CONCEPT.BIOSPECIMEN.ID',
        'Data Type': 'CONCEPT.GENOMIC_FILE.DATA_TYPE',
        'Filename': 'CONCEPT.GENOMIC_FILE.FILE_NAME',
        'Hashes': 'CONCEPT.GENOMIC_FILE.HASH_DICT',
        'Size': 'CONCEPT.GENOMIC_FILE.SIZE',
        'urls': 'CONCEPT.GENOMIC_FILE.URL_LIST',
    }
    df = df[list(col_rename.keys())]
    df.rename(columns=col_rename, inplace=True)
    return df


def get_genomic_file_sequencing_experiment_links(study_id):
    """
    Get the GenomicFile-Sequencing Experiment links at the DataService
    endpoint /sequencing-experiment-genomic-files by performing the following
    steps:
    1. Get the study's unharmonized genomic files
    2. Get the study's sequencing experiments
    3. Get the study's sequencing-experiment-genomic-file links
    4. Get the study's biospecimen-genomic-file links
    5. Join the tables from 1, 2, 3, 4 together on the genomic file ID
    Returns the table from step 5.
    """
    dfs = {}
    entity_types = {
        GENOMIC_FILES,
        SEQUENCING_EXPERIMENTS,
        SEQUENCING_EXPERIMENT_GENOMIC_FILES,
        BIOSPECIMEN_GENOMIC_FILES,
    }

    # Steps 1-4
    for entity_type in entity_types:
        dfs[entity_type] = get_entities(entity_type, study_id)

    # Step 5. Join tables 1-4 on genomic file ID. Some preprocessing needs to
    # be done first.
    
    # Start by merging the DataFrames from steps 1 and 3 on genomic-file ID
    dfs[SEQUENCING_EXPERIMENT]['_links.genomic_file'] = (
        dfs[SEQUENCING_EXPERIMENT]['_links.genomic_file'].apply(get_kf_id)
    )
    one_and_three = dfs[GENOMIC_FILES].merge(
        right=dfs[SEQUENCING_EXPERIMENT_GENOMIC_FILES],
        left_on='kf_id',
        right_on='_links.genomic_file',
        how='inner',
        suffixes=(None, '_SG')
    )

    # Then merge this result with Table 2 on sequencing-experiment ID
    one_and_three['_links.sequencing_experiment'] = (
        one_and_three['_links.sequencing_experiment'].apply(get_kf_id)
    )
    one_two_and_three = one_and_three.merge(
        right=dfs[SEQUENCING_EXPERIMENTS],
        left_on='_links.sequencing_experiment',
        right_on='kf_id',
        how='inner',
        suffixes=(None, '_SE')
    )

    # Merge this result with Table 4 on genomic-file ID
    dfs[BIOSPECIMEN_GENOMIC_FILES]['_links.genomic_file'] = (
        dfs[BIOSPECIMEN_GENOMIC_FILES]['_links.genomic_file'].apply(get_kf_id)
    )
    all_four = one_two_and_three.merge(
        right=dfs[BIOSPECIMEN_GENOMIC_FILES],
        left_on='kf_id',
        right_on='_links.genomic_file',
        how='inner',
        suffixes=(None, '_BG')
    )

    return all_four


def get_kf_id(link):
    """
    The links given by the DataService yield strings of the form
    /entity-type/kf_id. This function will return the kf_id.
    """
    return link.split('/')[-1]


def get_entities(entity_type, study_id):
    """
    Queries the DataService for the _entities_ associated with the _study_id_
    study. The full results are put into a DataFrame and returned. This
    DataFrame is formed using pandas.json_normalize() which flattens JSONs
    but may return data that aren't in exactly the form needed for ingestion.
    For example, values which are lists will be put into DataFrame entries that
    are lists, even if there's only a single value in the list. Processing
    for ingestion needs to be done on a case-by-case basis depending on the
    entity type in question.
    """
    args = {
        "study_id": study_id,
        "visible": True
    }
    if entity_type == GENOMIC_FILES:
        args["is_harmonized"] = False

    entities = yield_entities(
        DATASERVICE_URL,
        entity_type,
        args,
    )

    df = pd.json_normalize(entities)
    return df
