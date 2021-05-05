from creator.ingest_runs.utils import (
    fetch_s3_obj_info,
    scrape_s3,
    get_entities,
)

import pandas as pd


def test_fetch_s3_obj_info(mocker):
    """
    Test the _fetch_s3_obj_info_ function. This is a wrapper for
    _d3b_utils.aws_buckets_contents.fetch_aws_bucket_obj_info_.
    """
    mock_fetch = mocker.patch(
        "creator.ingest_runs.utils.fetch_aws_bucket_obj_info",
        return_value=[{"Key": "s3://test/test.md5"}],
    )

    BUCKET = "test_bucket"
    df = fetch_s3_obj_info(BUCKET)
    mock_fetch.assert_called_once()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_scrape_s3(mocker):
    """
    Test the _scrape_s3_ function. This calls _fetch_s3_object_info_ which
    needs to be mocked.
    """
    return_df = pd.DataFrame([{"Key": "s3://test/test.md5"}])
    mock_fetch = mocker.patch(
        "creator.ingest_runs.utils.fetch_s3_obj_info", return_value=return_df
    )
    BUCKETS = ["test_bucket"] * 2
    df = scrape_s3(BUCKETS)
    assert mock_fetch.call_count == 2
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_get_entities(mocker):
    """
    Test the _get_entities_ function. This is a wrapper for
    _kf_utils.dataservice.scrape.yield_entities_.
    """
    mock_yield = mocker.patch(
        "creator.ingest_runs.utils.yield_entities",
    )
    LOCALHOST = "http://localhost:5000"
    GEN_FILES = "genomic-files"
    STUDY_ID = "SD_ME0WME0W"
    get_entities(LOCALHOST, GEN_FILES, STUDY_ID)
    mock_yield.assert_called_once()
    base_url, endpoint, filter_dict = mock_yield.call_args_list[0][0]
    assert base_url == LOCALHOST
    assert endpoint == GEN_FILES
    assert filter_dict == {"study_id": STUDY_ID, "visible": True}
