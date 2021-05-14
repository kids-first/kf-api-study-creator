import os
import jsonpickle

import pytest

from django.core.files.base import ContentFile

from creator.analyses.analyzer import analyze_version
from creator.files.models import File, Version
from creator.analyses.file_types import FILE_TYPES
from creator.ingest_runs.tasks import validation_run
from creator.ingest_runs.factories import ValidationRunFactory
from creator.ingest_runs.models import ValidationResultset, State

from tests.extract_configs.fixtures import (
    make_template_df,
    MockVersion,
    MockAnalysis,
)

DATA_REVIEW_FILE_TYPES = ["PDA", "PTD", "PTP", "SAM", "S3S", "FTR"]


@pytest.fixture
def template_version(db, tmpdir, settings):
    """
    Return a function that uploads content to a version and produces an
    analysis for the version. The content will conform to a templated
    file type
    """

    def make_template_version(
        file_type, filename, version=None, file=None, study=None
    ):
        """
        Upload file content, create version analysis so cols are accessible
        on the file version during inspection
        """
        if version:
            pass
        elif file:
            version = file.versions.first()
        else:
            file = File(file_type=file_type, name=file_type, study=study)
            file.save()
            version = Version(
                file_name=filename, key=filename, size=100, root_file=file
            )
            version.save()

        df = make_template_df(file_type)
        df_content = df.to_csv(sep="\t", index=False)

        settings.BASE_DIR = os.path.join(tmpdir, "test")
        version.root_file.file_type = file_type
        version.root_file.save()
        version.key.save(filename, ContentFile(df_content))

        analysis = analyze_version(version)
        analysis.creator = version.creator
        analysis.save()

        version.refresh_from_db()

        assert os.path.exists(version.key.path)
        assert file_type in version.valid_types

        return version

    return make_template_version


@pytest.fixture
def data_review_with_files(db, template_version, data_review):
    """
    Upload content (that matches available extract configs) to the
    versions in the data_review
    """
    versions = []
    for ft in DATA_REVIEW_FILE_TYPES:
        versions.append(
            template_version(ft, f"{ft}.tsv", study=data_review.study)
        )
    data_review.versions.set(versions)
    data_review.save()
    data_review.validation_resultset.delete()
    data_review.refresh_from_db()

    return data_review


def test_run_validation_success(db, clients, mocker, data_review_with_files):
    """
    End to end test of run_validation task
    """
    vr = ValidationRunFactory(
        data_review=data_review_with_files, state=State.INITIALIZING
    )
    validation_run.run_validation(str(vr.pk))
    vr.refresh_from_db()
    assert vr.state == State.COMPLETED
    assert not vr.error_msg


def test_run_validation_fail(db, clients, mocker, data_review):
    """
    Test run_validation on failure
    """
    ER_MSG = "Error"
    mocker.patch(
        "creator.ingest_runs.tasks.validation_run.validate_file_versions",
        side_effect=Exception(ER_MSG),
    )
    vr = ValidationRunFactory(
        data_review=data_review, state=State.INITIALIZING
    )
    with pytest.raises(Exception):
        validation_run.run_validation(str(vr.pk))
    vr.refresh_from_db()
    assert not vr.success
    assert vr.state == State.FAILED
    assert vr.error_msg == ER_MSG


def test_validate_and_build_report(db, mocker, data_review_with_files):
    """
    Test file validation and report building
    """
    # Validate versions with extract configs
    versions = data_review_with_files.versions.all()
    vr = ValidationRunFactory(data_review=data_review_with_files)
    results = validation_run.validate_file_versions(vr)

    # Check that all versions for the review were validated
    assert results
    assert set(results["files_validated"]) == {v.kf_id for v in versions}
    report = validation_run.build_report(results)
    for ft in DATA_REVIEW_FILE_TYPES:
        assert FILE_TYPES[ft]["name"] in report

    # Test validation when all versions are missing extract cfgs
    mock_clean_map = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.clean_and_map",
        return_value=None,
    )
    ER_MSG = "No templates were found"
    with pytest.raises(Exception) as e:
        validation_run.validate_file_versions(vr)
        assert ER_MSG in str(e)


def test_persist_results(db, tmpdir, settings, data_review):
    """
    Test persistence of validation results
    """
    # Setup test data
    settings.BASE_DIR = os.path.join(tmpdir, "test")
    persist_results = validation_run.persist_results
    data_review.validation_resultset.delete()
    vr = ValidationRunFactory(data_review=data_review)
    results = {
        "validation": [
            {"type": "count", "is_applicable": False, "errors": []},
            {
                "type": "relationship",
                "is_applicable": True,
                "errors": [
                    {
                        "from": ("participant", "p1"),
                        "to": ("biospecimen", "b1"),
                    }
                ],
            },
            {"type": "attribute", "is_applicable": True, "errors": []},
        ]
    }
    report_markdown = "my validation report"

    # Persist results - first time for data review
    assert ValidationResultset.objects.count() == 0
    vrs = persist_results(results, report_markdown, vr)
    assert ValidationResultset.objects.count() == 1
    new_vrs = ValidationResultset.objects.get(pk=vrs.pk)
    assert new_vrs.passed == 1
    assert new_vrs.failed == 1
    assert new_vrs.did_not_run == 1
    assert not vr.success
    assert vr.progress == 1
    with open(new_vrs.report_file.path) as f:
        assert report_markdown == f.read()
    with open(new_vrs.results_file.path) as f:
        assert results == jsonpickle.decode(f.read(), keys=True)

    # Persist results - second time should be an update
    report_markdown = "new report markdown"
    results["validation"][1]["errors"] = []
    vrs = persist_results(results, report_markdown, vr)
    vr.refresh_from_db()
    assert ValidationResultset.objects.count() == 1
    vrs = ValidationResultset.objects.get(pk=vrs.pk)
    assert vrs.passed == 2
    assert vrs.failed == 0
    assert vrs.did_not_run == 1
    assert vr.success
    assert vr.progress == 1
    with open(vrs.report_file.path) as f:
        assert report_markdown == f.read()
    with open(vrs.results_file.path) as f:
        assert results == jsonpickle.decode(f.read(), keys=True)


def test_clean_and_map_errors(mocker):
    """
    Test the clean and map helper in the validation_run task
    """
    # Version missing a root file
    clean_and_map = validation_run.clean_and_map
    mock_version = MockVersion()
    mock_version.root_file = None
    with pytest.raises(Exception) as e:
        clean_and_map(mock_version)
        assert "missing root_file" in str(e)

    # Version missing an extract config
    assert clean_and_map(MockVersion(file_type="a file")) is None

    # Error extracting file content into DataFrame
    mocker.patch(
        "creator.ingest_runs.tasks.validation_run.extract_data",
        side_effect=Exception,
    )
    version = MockVersion(
        file_type="PDA", columns=FILE_TYPES["PDA"]["required_columns"]
    )
    with pytest.raises(Exception):
        clean_and_map(version)
