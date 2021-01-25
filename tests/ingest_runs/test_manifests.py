from creator.ingest_runs.manifests import (
    get_metadata,
    get_biospecimen_sequencing_experiment_links,
    load_entities,
    load_harmonized_genomic_files,
    munge_genomic_df,
    ingest_manifest,
)
from creator.ingest_runs.tasks import ingest_genomic_workflow_output_manifests
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.common.io import read_df

import pandas as pd
import pytest


@pytest.fixture
def manifest_df():
    return read_df('tests/data/SD_ME0WME0W/genomic-task/workflow.tsv')


@pytest.fixture
def genomic_df(manifest_df):
    s3_df = read_df('tests/data/SD_ME0WME0W/genomic-task/data/s3_scrape.csv')
    df = s3_df.merge(
        right=manifest_df,
        on='Filepath',
        how='inner',
    )
    return df


@pytest.fixture
def study_id():
    return 'SD_ME0WME0W'


def test_get_metadata(db, mocker, clients, manifest_df):
    """
    Test the _get_metadata_ function. Mainly just a sanity check.
    Requires being on the VPN with a current chop AWS token.
    """
    metadata_result = get_metadata(manifest_df)
    assert not metadata_result.empty
    assert manifest_df.shape == (10, 9)
    # Check that we got metadata for all the files in the original manifest.
    # We used an inner join, so any difference would imply we did not.
    assert manifest_df.shape[0] == metadata_result.shape[0]
    # Check that we get all the expected columns from the S3 scrape. The
    # columns from the manifest are guaranteed by the study-creator API.
    expected_columns = {
        'Filepath',
        'ETag',
        'Size',
        'Data Type',
        'KF Biospecimen ID',
    }
    assert expected_columns.issubset(metadata_result.columns)


def test_load_harmonized_genomic_files(
    db, mocker, clients, manifest_df, study_id, genomic_df
):
    """
    Test the loading of the harmonized genomic files from the manifest.
    """
    df = load_harmonized_genomic_files(genomic_df, study_id)
    assert not df.empty
    # Check no records are lost after the inner join
    assert genomic_df.shape[0] == df.shape[0]
    # Check that the columns are as expected
    expected_columns = {
        CONCEPT.BIOSPECIMEN.ID,
        CONCEPT.GENOMIC_FILE.DATA_TYPE,
        CONCEPT.GENOMIC_FILE.FILE_NAME,
        CONCEPT.GENOMIC_FILE.FILE_FORMAT,
        CONCEPT.GENOMIC_FILE.ID,
        CONCEPT.GENOMIC_FILE.HARMONIZED,
        CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
    }
    for column in expected_columns:
        assert column in df
        assert column not in genomic_df
    assert len(df.columns) == 7


def test_get_biospecimen_sequencing_experiment_links(
    db, mocker, clients, study_id
):
    """
    Test obtaining the biospecimen-sequencing-experiment links using
    _get_biospecimen_sequencing_experiment_links_. This function performs a lot
    of querying the DataService and DataFrame manipulation, but the result is
    simply a DataFrame with two columns. It isn't obvious how many rows we will
    have here, as it'll depend on how many Biospecimens there are total for the
    study. This number could be far larger than the number of harmonized
    genomic files that we are dealing with in this task.
    """
    df = get_biospecimen_sequencing_experiment_links(study_id)

    assert not df.empty
    # We should get 2 columns and 10 entries (there are 10 Biospecimens)
    assert df.shape == (10, 2)
    assert CONCEPT.BIOSPECIMEN.ID in df
    assert CONCEPT.SEQUENCING.ID in df

    # Check that none of the values are missing
    assert df[CONCEPT.BIOSPECIMEN.ID].notnull().all()
    assert df[CONCEPT.SEQUENCING.ID].notnull().all()

    # Check that the kf-ids are the appropriate type
    assert df[CONCEPT.BIOSPECIMEN.ID].apply(
        lambda x: x.startswith('BS_')
    ).all()

    assert df[CONCEPT.SEQUENCING.ID].apply(
        lambda x: x.startswith('SE_')
    ).all()


def test_ingest_genomic_workflow_output_manifests(db, mocker, clients):
    #TODO: After _ingest_genomic_workflow_output_manifests_ is implemented
    #ingest_genomic_workflow_output_manifests([])

    #Should this be here, or in test_tasks?
    pass


def test_ingest_manifest(
    db, mocker, clients, manifest_df, study_id, genomic_df
):
    """
    Test the full ingestion process carried out by _ingest_manifest_.
    """
    mock_get_metadata = mocker.patch(
        "creator.ingest_runs.manifests.get_metadata",
        return_value=genomic_df,
    )
    ingest_manifest(manifest_df, study_id)
    mock_get_metadata.assert_called_once()
    
