import ast
import boto3
import json
import os
import pandas as pd

from d3b_utils.aws_bucket_contents import fetch_aws_bucket_obj_info
from kf_lib_data_ingest.app import settings
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.common.io import read_df
from kf_lib_data_ingest.etl.load.load import LoadStage
from kf_utils.dataservice.scrape import yield_entities

from urllib.parse import urlparse


GEN_FILE = "genomic_file"
GEN_FILES = "genomic-files"
SEQ_EXPS = "sequencing-experiments"
SEQ_EXP_GEN_FILE = "sequencing_experiment_genomic_file"
SEQ_EXP_GEN_FILES = "sequencing-experiment-genomic-files"
BIO_GEN_FILE = "biospecimen_genomic_file"
BIO_GEN_FILES = "biospecimen-genomic-files"
# LOCALHOST = "http://dataservice:80" #for use with stack
LOCALHOST = "http://localhost:5000" # testing
DATASERVICE_URL = LOCALHOST # During testing


def ingest_manifest(manifest_df, study_id):
    """
    Performs the full ingest process for a genomic workflow manifest _version_.
    Returns the DataFrame used for loading, which is useful for testing.
    """
    # Need to use _extract_data_ method on Version, but not sure exactly how
    # this works. It doesn't work with any of the Versions in the django shell.
    # How was it tested?
    #TODO: just use a manifest_df for now

    genomic_df = get_metadata(manifest_df)
    genomic_df = load_harmonized_genomic_files(genomic_df, study_id)
    all_four = get_biospecimen_sequencing_experiment_links(study_id)
    # Join genomic_df and all_four on biospecimen ID, then load
    assert CONCEPT.BIOSPECIMEN.ID in genomic_df
    assert CONCEPT.BIOSPECIMEN.ID in all_four
    genomic_seq_df = genomic_df.merge(
        right=all_four,
        on=CONCEPT.BIOSPECIMEN.ID,
        how='inner',
    )
    df = genomic_seq_df[[
        CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
        CONCEPT.SEQUENCING.ID,
        CONCEPT.GENOMIC_FILE.ID,
        CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
    ]]
    df.drop_duplicates(inplace=True)
    df[CONCEPT.SEQUENCING.TARGET_SERVICE_ID] = df[CONCEPT.SEQUENCING.ID]
    df[CONCEPT.SEQUENCING_GENOMIC_FILE.VISIBLE] = True

    # Load the genomic-file sequencing-experiment links
    _ = load_entities(SEQ_EXP_GEN_FILE, df, study_id)
    return df


def get_metadata(manifest_df):
    """
    Scrape the metadata for each file in the manifest from S3, put it into a
    DataFrame, join this with _manifest_df_ on Filepath, and return it.
    """
    assert not manifest_df.empty, "Empty manifest DataFrame"
    assert "Filepath" in manifest_df.columns, "Missing Filepath column"

    buckets = set(os.path.split(row)[0] for row in manifest_df["Filepath"])
    file_df = scrape_s3(buckets)

    genomic_df = manifest_df.merge(right=file_df, on="Filepath", how="inner")
    return genomic_df


def scrape_s3(buckets):
    """
    Perform the scrape for each bucket in _buckets_. Return a DataFrame _df_
    which has all this data.
    """
    dfs = []
    for bucket in buckets:
        parsed_s3 = urlparse(bucket)
        bucket_df = pd.DataFrame(
            fetch_bucket_obj_info(
                bucket_name=parsed_s3.netloc,
                search_prefixes=parsed_s3.path,
                drop_folders=True,
            )
        )
        bucket_df["Filepath"] = f"s3://{parsed_s3.netloc}/" + bucket_df["Key"]
        dfs.append(bucket_df)

    df = pd.concat(dfs)
    df["Filename"] = df["Key"].map(lambda x: os.path.split(x)[-1])
    return df


def load_harmonized_genomic_files(genomic_df, study_id):
    """
    Load data for the harmonized genomic files found in the manifest into the
    DataService (this data is in _genomic_df_).
    This step must occur before the others so that we can use the
    kf_ids created here for the rest of the process. After ingestion, grab the
    generated kf_ids from the ingest lib cache, join them to _genomic_df_.
    Then use _genomic_df_ to create genomic-file biospecimen links and load
    them as well. Return _genomic_df_.
    """
    genomic_df = munge_genomic_df(genomic_df)
    genomic_cache = load_entities(
        GEN_FILE,
        genomic_df.drop(CONCEPT.BIOSPECIMEN.ID, axis=1),
        study_id,
    )
    genomic_df = get_genomic_file_kf_ids(genomic_cache, genomic_df)
    
    biospec_gen_df = genomic_df[[
        CONCEPT.GENOMIC_FILE.ID,
        CONCEPT.BIOSPECIMEN.ID,
        CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
    ]]
    biospec_gen_df[CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID] = biospec_gen_df[
        CONCEPT.BIOSPECIMEN.ID
    ]
    biospec_gen_df[CONCEPT.BIOSPECIMEN_GENOMIC_FILE.VISIBLE] = True

    # Create genomic-file biospecimen links
    _ = load_entities(BIO_GEN_FILE, biospec_gen_df, study_id)
    return genomic_df


def get_genomic_file_kf_ids(genomic_cache, genomic_df):
    """
    Takes genomic_df and appends the genomic-file kf-ids which are created
    after they're ingested. The ingest library stores the kf-ids in a cache
    which we must query. Returns genomic_df with a new kf-id column.
    """
    cache_dict = {
        ast.literal_eval(key)['external_id']: value
        for key, value in genomic_cache[GEN_FILE].items()
    }
    hash_df = pd.DataFrame(
        list(cache_dict.items()),
        columns=[
            CONCEPT.GENOMIC_FILE.ID, CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID
        ],
    )
    genomic_df = genomic_df.merge(
        right=hash_df,
        on=CONCEPT.GENOMIC_FILE.ID,
        how='inner',
    )
    return genomic_df


def load_entities(entity_type, df, study_id):
    """
    Load data of type _entity_type_ into the DataService from _df_.
    """
    target_service_base_url = LOCALHOST
    app_settings = settings.load()
    loader = LoadStage(
        app_settings.TARGET_API_CONFIG,
        target_service_base_url,
        [entity_type],
        study_id,
        cache_dir=os.getcwd(),
    )
    loader.run({entity_type: df})

    return loader.uid_cache


def munge_genomic_df(df):
    """
    Clean up the genomic-file DataFrame and get it ready to be ingested by
    removing unneeded columns and standardizing the column names.
    """
    df['Hashes'] = df.apply(lambda row: {"ETag": row['ETag']}, axis=1)
    df['urls'] = df.apply(lambda row: [row['Filepath']], axis=1)
    df['file_type'] = df.apply(
        lambda row: os.path.splitext(row['Filename'])[1][1:],
        axis=1,
    )
    col_rename = {
        'KF Biospecimen ID': CONCEPT.BIOSPECIMEN.ID,
        'Data Type': CONCEPT.GENOMIC_FILE.DATA_TYPE,
        'Filename': CONCEPT.GENOMIC_FILE.FILE_NAME,
        'Hashes': CONCEPT.GENOMIC_FILE.HASH_DICT,
        'Size': CONCEPT.GENOMIC_FILE.SIZE,
        'urls': CONCEPT.GENOMIC_FILE.URL_LIST,
        'file_type': CONCEPT.GENOMIC_FILE.FILE_FORMAT,
        'Filepath': CONCEPT.GENOMIC_FILE.ID,
    }
    df = df[list(col_rename.keys())]
    df.rename(columns=col_rename, inplace=True)
    df[CONCEPT.GENOMIC_FILE.HARMONIZED] = True
    return df


def get_biospecimen_sequencing_experiment_links(study_id):
    """
    Get the Biospecimen-Sequencing Experiment links by performing the following
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
        GEN_FILES,
        SEQ_EXPS,
        SEQ_EXP_GEN_FILES,
        BIO_GEN_FILES,
    }

    # Steps 1-4
    for entity_type in entity_types:
        dfs[entity_type] = get_entities(entity_type, study_id)

    # Step 5. Join tables 1-4 on genomic file ID. Some preprocessing needs to
    # be done first.
    
    # Start by merging the DataFrames from steps 1 and 3 on genomic-file ID
    GEN_LINK = '_links.genomic_file'

    # Check the validity of the SEQ_EXP_GEN_FILES DataFrame
    assert (
        GEN_LINK in dfs[SEQ_EXP_GEN_FILES], missing_data(SEQ_EXP_GEN_FILES)
    )
    #TODO: Do we want to check here that all values for genomic-file ID are
    #valid? Or should we just report that some are missing?
    dfs[SEQ_EXP_GEN_FILES][GEN_LINK] = (
        dfs[SEQ_EXP_GEN_FILES][GEN_LINK].map(get_kf_id)
    )
    assert 'kf_id' in dfs[GEN_FILES], missing_data(GEN_FILES)
    assert (
        GEN_LINK in dfs[SEQ_EXP_GEN_FILES], missing_data(SEQ_EXP_GEN_FILES)
    )
    one_and_three = dfs[GEN_FILES].merge(
        right=dfs[SEQ_EXP_GEN_FILES],
        left_on='kf_id',
        right_on=GEN_LINK,
        how='inner',
        suffixes=(None, '_SG')
    )

    # Then merge this result with Table 2 on sequencing-experiment ID
    SEQ_LINK = '_links.sequencing_experiment' 
    one_and_three[SEQ_LINK] = one_and_three[SEQ_LINK].map(get_kf_id)
    one_two_and_three = one_and_three.merge(
        right=dfs[SEQ_EXPS],
        left_on=SEQ_LINK,
        right_on='kf_id',
        how='inner',
        suffixes=(None, '_SE')
    )

    # Merge this result with Table 4 on genomic-file ID
    dfs[BIO_GEN_FILES][GEN_LINK] = dfs[BIO_GEN_FILES][GEN_LINK].map(get_kf_id)
    all_four = one_two_and_three.merge(
        right=dfs[BIO_GEN_FILES],
        left_on='kf_id',
        right_on=GEN_LINK,
        how='inner',
        suffixes=(None, '_BG')
    )

    # We need biospecimen ID, sequencing experiment ID,
    # and sequencing center ID
    col_rename = {
        'kf_id_SE': CONCEPT.SEQUENCING.ID,
        '_links.biospecimen': CONCEPT.BIOSPECIMEN.ID,
        '_links.sequencing_center': CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
    }

    # Reduce down to the needed columns and get them into standard form
    all_four = all_four[list(col_rename.keys())]
    all_four.rename(columns=col_rename, inplace=True)
    all_four[CONCEPT.BIOSPECIMEN.ID] = all_four[CONCEPT.BIOSPECIMEN.ID].map(
        get_kf_id
    )
    all_four[CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID] = all_four[
        CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID
    ].map(get_kf_id)
    return all_four


def missing_data(entity):
    return f"{entity} entries missing data"


def get_kf_id(link):
    """
    The links given by the DataService yield strings of the form
    /entity-type/kf_id. This function will return the kf_id.
    """
    return link.split('/')[-1]


def get_entities(
    entity_type, study_id, is_harmonized=False, target=DATASERVICE_URL
):
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
    if entity_type == GEN_FILES:
        args["is_harmonized"] = is_harmonized

    entities = list(yield_entities(
        target,
        entity_type,
        args,
    ))

    return pd.json_normalize(entities)
