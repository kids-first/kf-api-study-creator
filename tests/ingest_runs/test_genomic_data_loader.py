from creator.ingest_runs.genomic_data_loader import (
    GenomicDataLoader,
    GEN_FILE,
    GEN_FILES,
    SEQ_EXP,
    SEQ_EXPS,
    SEQ_EXP_GEN_FILE,
    SEQ_EXP_GEN_FILES,
    BIO_GEN_FILE,
)
from creator.studies.models import Study
from tests.integration.fixtures import test_study_generator  # noqa F401

from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.load.load import LoadStage

import ast
from django.conf import settings
import os
import pandas as pd
import pytest


FAKE_STUDY = Study()
FAKE_STUDY.study_id = "SD_YE0WYE0W"

GF_EXPECTED_COLUMNS = {
    CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
    CONCEPT.GENOMIC_FILE.DATA_TYPE,
    CONCEPT.GENOMIC_FILE.FILE_NAME,
    CONCEPT.GENOMIC_FILE.HASH_DICT,
    CONCEPT.GENOMIC_FILE.SIZE,
    CONCEPT.GENOMIC_FILE.URL_LIST,
    CONCEPT.GENOMIC_FILE.FILE_FORMAT,
    CONCEPT.GENOMIC_FILE.ID,
    CONCEPT.GENOMIC_FILE.SOURCE_FILE,
    CONCEPT.GENOMIC_FILE.HARMONIZED,
    CONCEPT.GENOMIC_FILE.VISIBLE,
}


@pytest.fixture
def study_generator(test_study_generator):  # noqa F811
    """
    Generates and returns the realistic fake study.
    """
    sg = test_study_generator(study_id=FAKE_STUDY.study_id, total_specimens=5)
    sg.ingest_study(dry_run=True)

    # Perform mapping operations for mocking _utils.get_entities_.
    sg.fake_entities = {}
    # Genomic-files
    gf_data = [
        entry
        for _, entry in sg.dataservice_payloads[GEN_FILE].items()
        if entry["is_harmonized"] == "False"
    ]
    sg.fake_entities[GEN_FILES] = pd.DataFrame(gf_data)
    # Sequencing-experiments
    seq_exp_rows = []
    for key, value in sg.cache[SEQ_EXP].items():
        row_dict = {
            "kf_id": value,
            "external_id": ast.literal_eval(key)["external_id"],
            "_links.sequencing_center": (
                ast.literal_eval(key)["sequencing_center_id"]
            ),
        }
        seq_exp_rows.append(row_dict)
    sg.fake_entities[SEQ_EXPS] = pd.DataFrame(seq_exp_rows)
    # Sequencing-experiments-genomic-files
    seq_exp_gf_rows = []
    for key in sg.cache[SEQ_EXP_GEN_FILE]:
        row_dict = {
            "_links.sequencing_experiment": (
                ast.literal_eval(key)["sequencing_experiment_id"]
            ),
            "_links.genomic_file": ast.literal_eval(key)["genomic_file_id"],
        }
        seq_exp_gf_rows.append(row_dict)
    sg.fake_entities[SEQ_EXP_GEN_FILES] = pd.DataFrame(seq_exp_gf_rows)
    return sg


@pytest.fixture
def mock_s3_scrape(mocker, study_generator):
    """
    Mock for creator.ingest_runs.genomic_data_loader.utils.scrape_s3.
    """
    df = study_generator.dataframes["s3_harmonized_gf_manifest.tsv"]
    df["Filename"] = df["Key"].map(lambda x: os.path.split(x)[-1])
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.utils.scrape_s3",
        return_value=df,
    )
    return mock


@pytest.fixture
def mock_get_entities(mocker, study_generator):
    """
    Mock for creator.ingest_runs.utils.get_entities
    """

    def fake_get_entities(*args, **kwargs):
        entity_type = args[1]
        return study_generator.fake_entities[entity_type]

    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.utils.get_entities",
        side_effect=fake_get_entities,
    )
    return mock


@pytest.fixture
def mock_load_entities(tmpdir, mocker, study_generator):
    """
    Mock for GenomicDataLoader._load_entities function which allows testing to
    occur without the use of the DataService.
    """

    def _dry_load_entities(*args, **kwargs):
        """
        Inserts KF IDs into output of _load_entities
        """
        from kf_lib_data_ingest.app.settings.base import TARGET_API_CONFIG

        entity_type = args[0]
        loader = LoadStage(
            TARGET_API_CONFIG,
            settings.DATASERVICE_URL,
            [entity_type],
            study_generator.study_id,
            cache_dir=os.path.join(tmpdir, "temp"),
            dry_run=True,
        )
        loader.run({entity_type: args[1]})
        return loader.uid_cache

    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "_load_entities",
        side_effect=_dry_load_entities,
    )
    return mock


@pytest.fixture
def mock_load_bs_gf_links(mocker):
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "load_specimen_harmonized_gf_links"
    )
    return mock


@pytest.fixture
def mock_load_se_gf_links(mocker):
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "load_seq_exp_harmonized_genomic_files"
    )
    return mock


@pytest.fixture
def mock_validate(mocker):
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "_validate_load"
    )
    return mock


def test_load_harmonized_genomic_files(
    mock_s3_scrape, study_generator, mock_load_entities
):
    """
    Test the loading of the harmonized genomic files from the genomic workflow
    output manifest.
    """
    loader = GenomicDataLoader(FAKE_STUDY)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    loader.load_harmonized_genomic_files(manifest_df)
    mock_s3_scrape.assert_called_once()
    mock_load_entities.assert_called_once()
    entity_type, df = mock_load_entities.call_args_list[0][0]
    assert isinstance(df, pd.DataFrame)
    assert entity_type == GEN_FILE
    assert not df.empty

    manifest_df = manifest_df.drop_duplicates(["Filepath"])
    assert manifest_df.shape[0] == df.shape[0]
    # Check that the columns are as expected
    for column in GF_EXPECTED_COLUMNS:
        assert column in df
    assert df.shape[1] == len(GF_EXPECTED_COLUMNS)


def test_load_specimen_harmonized_gf_links(
    study_generator, mock_s3_scrape, mock_load_entities
):
    """
    Test the load_specimen_harmonized_gf_links function. This is the second
    step of the ingestion process.
    """
    loader = GenomicDataLoader(FAKE_STUDY)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    gfs = loader.load_harmonized_genomic_files(manifest_df)
    loader.load_specimen_harmonized_gf_links(gfs)
    mock_s3_scrape.assert_called_once()
    assert mock_load_entities.call_count == 2
    # Now check the biospecimen gf links loading
    entity_type2, df2 = mock_load_entities.call_args_list[1][0]
    assert entity_type2 == BIO_GEN_FILE
    assert isinstance(df2, pd.DataFrame)
    assert not df2.empty
    manifest_df = manifest_df.drop_duplicates(["Filepath"])
    assert manifest_df.shape[0] == df2.shape[0]
    expected_columns = {
        CONCEPT.GENOMIC_FILE.ID,
        CONCEPT.BIOSPECIMEN.TARGET_SERVICE_ID,
        CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
        CONCEPT.BIOSPECIMEN.ID,
        CONCEPT.BIOSPECIMEN_GENOMIC_FILE.VISIBLE,
    }
    for col in expected_columns:
        assert col in df2
    assert df2.shape[1] == len(expected_columns)


def test_get_seq_experiment_genomic_files(study_generator, mock_get_entities):
    """
    Test the _get_seq_experiment_genomic_files_ function. This can be done in
    isolation.
    """
    loader = GenomicDataLoader(FAKE_STUDY)
    output = loader._get_seq_experiment_genomic_files()
    # Check _get_entities_ was called the right number of times and the output
    # is as we expect
    assert mock_get_entities.call_count == 3
    expected_columns = {
        CONCEPT.SEQUENCING.TARGET_SERVICE_ID,
        CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
        CONCEPT.SEQUENCING.ID,
        CONCEPT.GENOMIC_FILE.SOURCE_FILE,
    }
    for col in expected_columns:
        assert col in output
    assert output.shape[1] == len(expected_columns)
    gfs = study_generator.dataservice_payloads[GEN_FILE]
    harm_gf = [
        key for key, value in gfs.items() if value["is_harmonized"] == "False"
    ]
    assert output.shape[0] == len(harm_gf)


def test_load_seq_exp_harmonized_genomic_files(
    study_generator,
    mock_s3_scrape,
    mock_load_entities,
    mock_get_entities,
    mock_validate,
):
    """
    Test the _load_seq_exp_harmonized_genomic_files_ function. Here no steps of
    the ingest process are mocked, so this is really testing the entire
    process.
    """
    loader = GenomicDataLoader(FAKE_STUDY)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    output_df = loader.ingest_gwo(manifest_df)
    mock_s3_scrape.assert_called_once()

    # Check that _load_entities_ was called the right number of times
    assert mock_load_entities.call_count == 3
    # Check sequencing-experiment-genomic-files for the harmonized
    # files are loaded properly
    entity_type, df = mock_load_entities.call_args_list[2][0]
    assert entity_type == SEQ_EXP_GEN_FILE
    assert isinstance(df, pd.DataFrame)
    manifest_df = manifest_df.drop_duplicates(["Filepath"])
    assert not df.empty
    assert manifest_df.shape[0] == df.shape[0]
    expected_columns = {
        CONCEPT.SEQUENCING.TARGET_SERVICE_ID,
        CONCEPT.SEQUENCING.CENTER.TARGET_SERVICE_ID,
        CONCEPT.SEQUENCING_GENOMIC_FILE.VISIBLE,
        CONCEPT.SEQUENCING.ID,
        CONCEPT.GENOMIC_FILE.TARGET_SERVICE_ID,
    }.union(GF_EXPECTED_COLUMNS)
    for col in expected_columns:
        assert col in df
    total_column_len = len(expected_columns)
    assert df.shape[1] == total_column_len

    # Finally check output of the ingest process is as expected
    assert isinstance(output_df, pd.DataFrame)
    assert not output_df.empty
    assert output_df.shape[0] == manifest_df.shape[0]
    # The columns should be the same as the input to the previous step
    for col in expected_columns:
        assert col in output_df
    assert output_df.shape[1] == total_column_len
