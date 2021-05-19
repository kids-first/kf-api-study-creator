from creator.ingest_runs.genomic_data_loader import (
    GenomicDataLoader,
    GEN_FILE,
    GEN_FILES,
    SEQ_EXP,
    SEQ_EXPS,
    SEQ_EXP_GEN_FILE,
    SEQ_EXP_GEN_FILES,
    BIO_GEN_FILE,
    BIOSPECIMENS,
    GWO_MANIFEST,
)
from creator.events.models import Event
from creator.ingest_runs.models import IngestRun
from creator.fields import kf_id_generator
from creator.files.models import File
from creator.studies.factories import StudyFactory
from tests.integration.fixtures import test_study_generator  # noqa F401

from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.load.load_v2 import LoadStage

import ast
from django.conf import settings
from django.contrib.auth import get_user_model
import logging
import os
import pandas as pd
import pytest

logger = logging.getLogger(__name__)
logger.propagate = True

User = get_user_model()

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
def FAKE_STUDY(db):
    study = StudyFactory(kf_id="SD_YE0WYE0W")
    study.save()
    return study


@pytest.fixture
def ingest_run(db, prep_file):
    # Setup an IngestRun
    user = User.objects.first()
    prep_file(authed=True)
    file_versions = [File.objects.first().versions.first()]
    ir = create_ir(file_versions, user)
    return ir


@pytest.fixture
def study_generator(test_study_generator, FAKE_STUDY):  # noqa F811
    """
    Generates and returns the realistic fake study.
    """
    NUM_SPECIMENS = 5
    sg = test_study_generator(
        study_id=FAKE_STUDY.kf_id, total_specimens=NUM_SPECIMENS
    )
    sg.ingest_study(dry_run=True)

    # Perform mapping operations for mocking _utils.get_entities_.
    sg.fake_entities = {}
    # Genomic-files
    gf_data = [
        entry
        for entry in sg.dataservice_payloads[GEN_FILE].values()
        if entry["is_harmonized"] == "False"
    ]
    # The kf IDs the ingest library gives back during a dry run causes all
    # kinds of headaches. Replace them with random kf ids.
    gf_kf_ids = [kf_id_generator("GF") for _ in range(NUM_SPECIMENS * 3)]
    for gf_entry, kf_id in zip(gf_data, gf_kf_ids):
        gf_entry["kf_id"] = kf_id
    gwo_df = sg.dataframes["gwo_manifest.tsv"]
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
    for key, gen_kf_id in zip(sg.cache[SEQ_EXP_GEN_FILE], gf_kf_ids):
        row_dict = {
            "_links.sequencing_experiment": (
                ast.literal_eval(key)["sequencing_experiment_id"]
            ),
            "_links.genomic_file": gen_kf_id,
        }
        seq_exp_gf_rows.append(row_dict)
    sg.fake_entities[SEQ_EXP_GEN_FILES] = pd.DataFrame(seq_exp_gf_rows)
    # Biospecimens
    biospec_rows = [{"kf_id": value} for value in gwo_df["KF Biospecimen ID"]]
    sg.fake_entities[BIOSPECIMENS] = pd.DataFrame(biospec_rows)
    return sg


@pytest.fixture
def file_df(mocker, study_generator):
    df = study_generator.dataframes["s3_harmonized_gf_manifest.tsv"]
    df["Filename"] = df["Key"].map(lambda x: os.path.split(x)[-1])
    return df


@pytest.fixture
def mock_s3_scrape(mocker, study_generator, file_df):
    """
    Mock for creator.ingest_runs.genomic_data_loader.utils.scrape_s3.
    """
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.utils.scrape_s3",
        return_value=file_df,
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
    """
    Mock out the load_specimen_harmonized_gf_links method of
    GenomicDataLoader.
    """
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "load_specimen_harmonized_gf_links"
    )
    return mock


@pytest.fixture
def mock_load_se_gf_links(mocker):
    """
    Mock out the load_seq_exp_harmonized_genomic_files method of
    GenomicDataLoader.
    """
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "load_seq_exp_harmonized_genomic_files"
    )
    return mock


@pytest.fixture
def mock_validate(mocker):
    """
    Mock out the _validate_load method of GenomicDataLoader.
    """
    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "_validate_load"
    )
    return mock


@pytest.fixture
def mock_merge_and_validate(
    mocker, FAKE_STUDY, ingest_run, study_generator, file_df
):
    """
    Mock out the _merge_and_validate method of GenomicDataLoader.
    """
    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    return_value = loader._merge_and_validate(
        manifest_df, file_df, GWO_MANIFEST, "S3 bucket", on="Filepath"
    )

    mock = mocker.patch(
        "creator.ingest_runs.genomic_data_loader.GenomicDataLoader."
        "_merge_and_validate",
        return_value=return_value,
    )
    return mock


def test_load_harmonized_genomic_files(
    mock_s3_scrape,
    study_generator,
    mock_load_entities,
    FAKE_STUDY,
    ingest_run,
    mock_merge_and_validate,
    file_df,
):
    """
    Test the loading of the harmonized genomic files from the genomic workflow
    output manifest.
    """
    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    loader.load_harmonized_genomic_files(manifest_df)
    mock_s3_scrape.assert_called_once()

    mock_merge_and_validate.assert_called_once()
    merge_call_args = mock_merge_and_validate.call_args_list[0][0]
    merge_df1, merge_df2, name1, name2 = merge_call_args
    pd.testing.assert_frame_equal(merge_df1, manifest_df)
    pd.testing.assert_frame_equal(merge_df2, file_df)
    assert name1 == GWO_MANIFEST
    assert name2 == "S3 bucket"

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
    study_generator,
    mock_s3_scrape,
    mock_load_entities,
    mock_get_entities,
    FAKE_STUDY,
    ingest_run,
    mock_merge_and_validate,
):
    """
    Test the load_specimen_harmonized_gf_links function. This is the second
    step of the ingestion process.
    """
    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    gfs = loader.load_harmonized_genomic_files(manifest_df)
    loader.load_specimen_harmonized_gf_links(gfs)
    mock_s3_scrape.assert_called_once()

    assert mock_merge_and_validate.call_count == 2
    # The load_df arg here is the same as is tested below, so no need to
    # check it twice
    _, merge_df2, name1, name2 = mock_merge_and_validate.call_args_list[1][0]
    assert "kf_id" in merge_df2
    assert name1 == GWO_MANIFEST
    assert name2 == "DataService"

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


def test_get_seq_experiment_genomic_files(
    study_generator,
    mock_get_entities,
    mock_s3_scrape,
    mock_load_entities,
    FAKE_STUDY,
    ingest_run,
    mock_merge_and_validate,
):
    """
    Test the _get_seq_experiment_genomic_files_ function. This can be done in
    isolation.
    """
    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    gfs = loader.load_harmonized_genomic_files(manifest_df)
    output = loader._get_seq_experiment_genomic_files(gfs)

    assert mock_merge_and_validate.call_count == 3
    merge_call_args2 = mock_merge_and_validate.call_args_list[1][0]
    merge_df1, merge_df2, name1, name2 = merge_call_args2
    assert CONCEPT.GENOMIC_FILE.SOURCE_FILE in merge_df1
    assert CONCEPT.GENOMIC_FILE.SOURCE_FILE in merge_df2
    assert name1 == GWO_MANIFEST
    assert name2 == "DataService"
    merge_call_args3 = mock_merge_and_validate.call_args_list[2][0]
    merge_df3, merge_df4, name3, name4 = merge_call_args3
    assert "gf_kf_id" in merge_df3
    assert CONCEPT.SEQUENCING.TARGET_SERVICE_ID in merge_df4
    assert name3 == GWO_MANIFEST
    assert name4 == "DataService"

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
    unharm_gf = [
        key for key, value in gfs.items() if value["is_harmonized"] == "False"
    ]
    output = output.drop_duplicates(CONCEPT.GENOMIC_FILE.SOURCE_FILE)
    assert output.shape[0] == len(unharm_gf)


def test_load_seq_exp_harmonized_genomic_files(
    db,
    study_generator,
    mock_s3_scrape,
    mock_load_entities,
    mock_get_entities,
    mock_validate,
    caplog,
    ingest_run,
    FAKE_STUDY,
    mock_merge_and_validate,
):
    """
    Test the _load_seq_exp_harmonized_genomic_files_ function. Here no steps of
    the ingest process are mocked, so this is testing the entire process.
    """
    caplog.set_level(logging.WARNING)
    # Setup an IngestRun

    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    output_df = loader.ingest_gwo(manifest_df)
    output_df = output_df.drop_duplicates(CONCEPT.GENOMIC_FILE.ID)
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
    df = df.drop_duplicates(CONCEPT.GENOMIC_FILE.FILE_NAME)
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

    # Check that none of the missing data logging or Events occurred
    s3_msg = (
        f"records in the {GWO_MANIFEST} were not found in the " f"S3 bucket"
    )
    assert s3_msg not in caplog.text
    ds_msg = (
        f"records in the {GWO_MANIFEST} were not found in the " f"DataService"
    )
    assert ds_msg not in caplog.text
    assert Event.objects.filter(event_type="IR_MIS").count() == 0


def create_ir(file_versions, user):
    """
    The missing data Event creation only fires when
    GenomicDataLoader is provided an IngestRun. This is to keep the old tests
    compatible. This function will create and return one.
    """
    ir = IngestRun()
    ir.creator = user
    ir.save()
    ir.versions.set(file_versions)
    ir.save()
    return ir


def test_merge_and_validate(
    db, mocker, study_generator, caplog, prep_file, FAKE_STUDY, ingest_run
):
    """
    Test the _merge_and_validate method. For the purpose of testing, we'll
    manifest which doesn't have a corresponding entry in the S3 scrape.
    """
    caplog.set_level(logging.WARNING)

    loader = GenomicDataLoader(FAKE_STUDY, ingest_run)
    manifest_df = study_generator.dataframes["gwo_manifest.tsv"]
    extra_row = {column: "FAKE" for column in manifest_df.columns}
    manifest_df = manifest_df.append(extra_row, ignore_index=True)
    file_df = study_generator.dataframes["s3_harmonized_gf_manifest.tsv"]
    left_df_name = "GWO Manifest"
    right_df_name = "S3 Bucket"
    result = loader._merge_and_validate(
        manifest_df,
        file_df,
        left_df_name,
        right_df_name,
        on="Filepath",
    )
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    # The FAKE row should be lost
    assert manifest_df.shape[0] == result.shape[0] + 1
    # Check for logging and an Event
    msg = (
        f"1 records in the {left_df_name} were not found in the "
        f"{right_df_name}"
    )
    assert msg in caplog.text
    missing_evs = list(Event.objects.filter(event_type="IR_MIS"))
    assert len(missing_evs) == 1
    assert msg in missing_evs[0].description
