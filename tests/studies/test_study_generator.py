import os
import pytest
from unittest.mock import MagicMock
from pprint import pprint

from django.conf import settings

from creator.studies.data_generator.study_generator import (
    StudyGenerator,
    DEFAULT_STUDY_ID,
    DEFAULT_SPECIMENS
)
from kf_lib_data_ingest.app.settings.base import TARGET_API_CONFIG
STUDY_GENERATOR_MODULE = "creator.studies.data_generator.study_generator"


def test_end_to_end(mocker, tmpdir):
    """
    Test StudyGenerator.ingest_study in dry_run mode

    The dry_run mode runs the whole ingest pipeline except it doesn't
    actually send the payloads to Dataservice. If we can check that
    the correct payloads got constructed then we know StudyGenerator
    is working as expected.
    """
    mock_initalize = mocker.patch(
        f"{STUDY_GENERATOR_MODULE}.StudyGenerator.initialize_study"
    )
    # Happy case
    sg = StudyGenerator(working_dir=os.path.join(tmpdir, "temp"))
    sg.ingest_study(clean=True, verify_counts=True, dry_run=True)

    # Something went wrong - one participant didn't load
    sg.ingest_study(clean=True, verify_counts=False, dry_run=True)
    pts = sg.dataservice_payloads["participant"]
    first = list(pts.keys())[0]
    pts.pop(first)

    with pytest.raises(AssertionError) as e:
        sg._verify_counts(dry_run=True)
        assert f"{first} failed!"


@pytest.mark.parametrize(
    "clean,random_seed,verify_counts,dry_run",
    [
        (True, True, True, True),
        (False, False, False, True)
    ]
)
def test_ingest_study(
    mocker, tmpdir, clean, random_seed, verify_counts, dry_run
):
    """
    Test StudyGenerator.ingest_study
    """
    # Setup mock methods
    mocks = {
        method: mocker.patch(
            f"{STUDY_GENERATOR_MODULE}.StudyGenerator.{method}"
        )
        for method in [
            "clean", "generate_files", "run_ingest_pipeline", "_verify_counts"
        ]
    }
    mock_ra = mocker.patch(f"{STUDY_GENERATOR_MODULE}.ra")

    # Ingest
    sg = StudyGenerator(working_dir=os.path.join(tmpdir, "temp"))
    sg.ingest_study(
        clean=clean, random_seed=random_seed,
        verify_counts=verify_counts, dry_run=dry_run
    )

    # Check methods were called with right args
    if not random_seed:
        mock_ra.seed.assert_called_with(0)
    if clean:
        mocks["clean"].assert_called_with(dry_run=dry_run)
    if verify_counts:
        mocks["_verify_counts"].assert_called_with(dry_run=dry_run)
    mocks["run_ingest_pipeline"].assert_called_with(dry_run=dry_run)


def test_setup(tmpdir):
    """
    Test StudyGenerator constructor
    """
    def check_sg(sg, kwargs):
        for k, v in kwargs.items():
            assert getattr(sg, k) == v
        working_dir, ingest_package = os.path.split(sg.ingest_package_dir)
        assert ingest_package == f"{sg.study_id}_ingest_package"
        assert sg.data_dir == os.path.join(sg.ingest_package_dir, "data")
        assert sg.study_id.replace("_", "-").lower() in sg.study_bucket

    # Test defaults
    sg = StudyGenerator()
    defaults = {
        "dataservice_url": settings.DATASERVICE_URL,
        "total_specimens": DEFAULT_SPECIMENS,
        "working_dir": os.getcwd(),
        "study_id": DEFAULT_STUDY_ID,
    }
    check_sg(sg, defaults)

    # Test non-defaults
    kwargs = {
        "dataservice_url": "http://dataservice",
        "total_specimens": 5,
        "working_dir": os.path.join(tmpdir, "temp"),
        "study_id": "SD_YEOWYE0W",
    }
    sg = StudyGenerator(**kwargs)
    check_sg(sg, kwargs)


@pytest.mark.parametrize(
    "dry_run,all_studies",
    [(None, None), (True, False), (False, True), (True, True)]
)
def test_clean(mocker, tmpdir, dry_run, all_studies):
    """
    Test StudyGenerator.clean
    """
    mock_delete_entities = mocker.patch(
        f"{STUDY_GENERATOR_MODULE}.delete_entities"
    )
    mock_shutil = mocker.patch(f"{STUDY_GENERATOR_MODULE}.shutil")

    sg = StudyGenerator()
    sg.clean(dry_run=dry_run, all_studies=all_studies)
    sids = None if all_studies else [sg.study_id]

    # Check that dataservice ents not deleted in dry run mode
    if not dry_run:
        mock_delete_entities.assert_called_with(
            sg.dataservice_url, study_ids=sids
        )
    # Check generated ingest package is deleted
    mock_shutil.rmtree.assert_called_with(
        sg.ingest_package_dir, ignore_errors=True
    )


def test_generate_files(mocker, tmpdir):
    """
    Test StudyGenerator.generate_files
    """
    mock_read_df = mocker.patch(f"{STUDY_GENERATOR_MODULE}.read_df")

    # Check new files were created
    sg = StudyGenerator(working_dir=os.path.join(tmpdir, "temp"))
    sg.generate_files()
    assert mock_read_df.call_count == 0
    for fn in sg._df_creators:
        fp = os.path.join(sg.data_dir, fn)
        assert os.path.exists(fp)

    # Check existing files were read
    mock_write_dfs = mocker.patch(
        f"{STUDY_GENERATOR_MODULE}.StudyGenerator._write_dfs"
    )
    sg = StudyGenerator(working_dir=os.path.join(tmpdir, "temp"))
    sg.generate_files()
    assert mock_read_df.call_count == len(sg._df_creators)
    assert mock_write_dfs.call_count == 0


def test_dataframes():
    """
    Test DataFrame creation in StudyGenerator.generate_files
    """
    sg = StudyGenerator()
    sg._create_dfs()
    assert len(sg.dataframes) == 5
    for _, df in sg.dataframes.items():
        assert not df.empty
        assert df.shape[0] > 0


def test_initialize_study(mocker):
    """
    Test StudyGenerator.intialize_study
    """
    mock_session = mocker.patch(f"{STUDY_GENERATOR_MODULE}.Session")
    sg = StudyGenerator()
    sg.initialize_study()
    expected = {
        f"{sg.dataservice_url}/{e}"
        for e in ("studies", "sequencing-centers")
    }
    urls = {args[0] for args, _ in mock_session().post.call_args_list}
    assert urls == expected


def test_run_ingest_pipeline(mocker):
    """
    Test StudyGenerator.run_ingest_pipeline
    """
    # Setup mocks
    class LoadStage:
        sample_payload = {
            "type": "family",
            "host": "http://dataservice",
            "body": {
                "kf_id": "foo",
                "key": "value"
            }
        }

        def __init__(self):
            self.sent_messages = [self.sample_payload]

    class MockDataIngestPipeline(MagicMock):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.stages = {
                "LoadStage": LoadStage()
            }

    mock_init_study = mocker.patch(
        f"{STUDY_GENERATOR_MODULE}.StudyGenerator.initialize_study"
    )
    mock_ingest_pipeline = mocker.patch(
        f"{STUDY_GENERATOR_MODULE}.DataIngestPipeline",
        return_value=MockDataIngestPipeline()
    )

    # Run ingest pipeline
    sg = StudyGenerator()
    ingest_kwargs = {"dry_run": True}
    sg.run_ingest_pipeline(**ingest_kwargs)

    # Check ingest was run with prop args
    mock_init_study.call_count == 1
    mock_ingest_pipeline.assert_called_with(
        sg.ingest_package_dir, TARGET_API_CONFIG, **ingest_kwargs
    )
    mock_ingest_pipeline.data_ingest_config.study == sg.study_id
    mock_ingest_pipeline.run.call_count == 1

    # Check dataservice payloads were constructed properly
    p = LoadStage.sample_payload
    assert len(sg.dataservice_payloads[p["type"]]) == 1
    assert sg.dataservice_payloads[p["type"]][p["body"]["kf_id"]] == p["body"]
