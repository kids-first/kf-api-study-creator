import pytest
from creator.ingest_runs.manifests import (
    get_metadata,
    get_genomic_file_sequencing_experiment_links,
    munge_genomic_df,
    load_harmonized_genomic_files,
)
from kf_lib_data_ingest.common.io import read_df
from creator.ingest_runs.tasks import ingest_genomic_workflow_output_manifests


@pytest.fixture
def manifest_df():
    test_file = (
        f"~/Projects/kf-api-study-creator/creator/ingest_runs/"
        f"sample_genomic.tsv"
    )
    df = read_df(test_file)
    return df


def test_get_metadata(db, mocker, clients, manifest_df):
    """
    Test the _get_metadata_ function. Mainly just a sanity check.
    """
    metadata_result = get_metadata(manifest_df)
    assert not metadata_result.empty
    # Check that we got metadata for all the files in the original manifest.
    # We used an inner join, so any difference would imply we did not.
    assert manifest_df.shape[0] == metadata_result.shape[0]
    # Check that we get all the expected columns from the S3 scrape. The
    # columns from the manifest are guaranteed by the study-creator API.
    expected_columns = {
        "Filepath",
        "ETag",
        "Size",
        "Data Type",
        "KF Biospecimen ID",
    }
    assert expected_columns.issubset(metadata_result.columns)


def test_load_harmonized_genomic_files(db, mocker, clients, manifest_df):
    genomic_df = get_metadata(manifest_df)
    load_harmonized_genomic_files(genomic_df, 'SD_BHJXBDQK')
    assert False


def test_get_genomic_file_sequencing_experiment_links(db, mocker, clients):
    pass


def test_ingest_genomic_workflow_output_manifests(db, mocker, clients):
    ingest_genomic_workflow_output_manifests([])
