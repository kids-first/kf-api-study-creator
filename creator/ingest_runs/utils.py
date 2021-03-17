import os
import logging
from urllib.parse import urlparse

import pandas as pd

from d3b_utils.aws_bucket_contents import fetch_aws_bucket_obj_info
from kf_utils.dataservice.scrape import yield_entities

logger = logging.getLogger(__name__)


def fetch_s3_obj_info(bucket_name, search_prefixes=None):
    """
    Wrapper around d3b_utils.fetch_aws_obj_info. Adds filepath and filename
    to output df
    """
    df = pd.DataFrame(
        fetch_aws_bucket_obj_info(
            bucket_name=bucket_name,
            search_prefixes=search_prefixes
        )
    )
    # Filepath
    df["Filepath"] = f"s3://{bucket_name}/" + df["Key"]

    # Filter out folders
    df["Filename"] = df["Key"].map(lambda x: os.path.split(x)[-1])

    return df


def scrape_s3(buckets):
    """
    Fetch S3 object info (Size, ETag, etc) for objects in each bucket in
    _buckets_. Return a DataFrame _df_ with the resulting data.
    """
    dfs = []
    for bucket in buckets:
        logger.info(f"Scraping S3 bucket {bucket} for object info ...")
        parsed_s3 = urlparse(bucket)
        bucket_df = pd.DataFrame(
            fetch_s3_obj_info(
                bucket_name=parsed_s3.netloc,
                search_prefixes=[parsed_s3.path]
            )
        )
        dfs.append(bucket_df)
    df = pd.concat(dfs)

    logger.info(f"Found {df.shape[0]} objects")

    return df


def get_entities(base_url, endpoint, study_id, filter_dict=None):
    """
    Queries the DataService for the _entities_ associated with the _study_id_
    study. The full results are put into a DataFrame and returned.

    This DataFrame is formed using pandas.json_normalize() which flattens
    JSONs but may return data that aren't in exactly the form needed for
    ingestion. For example, values which are lists will be put into DataFrame
    entries that are lists, even if there's only a single value in the list.
    Processing for ingestion needs to be done on a case-by-case basis
    depending on the entity type in question.
    """
    if not filter_dict:
        filter_dict = {}

    filter_dict.update({
        "study_id": study_id,
        "visible": True
    })

    entities = list(yield_entities(base_url, endpoint, filter_dict))

    return pd.json_normalize(entities)
