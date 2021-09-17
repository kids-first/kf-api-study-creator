import os
import jsonpickle

import pytest
import pandas

from django.core.files.base import ContentFile

from creator.files.models import File, Version
from creator.ingest_runs.tasks import (
    validation_run,
)
from creator.data_templates.factories import (
    TemplateVersionFactory,
    TemplateVersion
)
from creator.studies.factories import StudyFactory
from creator.data_reviews.factories import DataReviewFactory
from creator.ingest_runs.factories import ValidationRunFactory
from creator.ingest_runs.models import ValidationResultset, State

from tests.extract_configs.fixtures import make_template_df

from pprint import pprint

DATA_REVIEW_FILE_TYPES = ["PDA", "PTD", "PTP", "BCM", "S3S", "FTR"]


@pytest.fixture
def file_version(db, tmpdir, settings):
    """
    Return a function that uploads content to a file version, creates a
    template to match the file content and attaches the template to the
    file version's root_file
    """

    def make_file_version(file_type, study=None):
        """
        Upload file content, create version analysis so cols are accessible
        on the file version during inspection
        """
        # Make file and first version
        filename = f"{file_type}.tsv"
        file = File(file_type=file_type, name=file_type, study=study)
        file.save()
        version = Version(
            file_name=filename, key=filename, size=100, root_file=file
        )
        version.save()

        # Add file version content
        df = make_template_df(file_type)
        df_content = df.to_csv(sep="\t", index=False)
        settings.BASE_DIR = os.path.join(tmpdir, "test")
        version.root_file.file_type = file_type
        version.root_file.save()
        version.key.save(filename, ContentFile(df_content))
        version.refresh_from_db()

        # Make a template version which matches the file version columns
        tv = TemplateVersionFactory()
        tv.field_definitions["fields"] = [
            {
                "label": c,
                "key": "|".join(c.split(" ")).upper(),
                "description": f"A description for {c}"
            }
            for c in df.columns
        ]
        tv.save()
        tv.data_template.name = f"{file_type} Template"
        tv.data_template.save()

        # Add template to study
        study.template_versions.add(tv)
        study.save()

        assert os.path.exists(version.key.path)

        return version

    return make_file_version


@pytest.fixture
def data_review_with_files(db, file_version, data_review):
    """
    Upload content (that matches available extract configs) to the
    versions in the data_review
    """
    versions = []
    for ft in DATA_REVIEW_FILE_TYPES:
        versions.append(
            file_version(ft, study=data_review.study)
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


def test_validate_template_errors(db, mocker, data_review_with_files):
    """
    Test validation_run.validate_file_versions template errors
    """
    # Study with no templates
    dr = DataReviewFactory(study=StudyFactory())
    vr = ValidationRunFactory(data_review=dr)
    with pytest.raises(TemplateVersion.DoesNotExist) as e:
        results = validation_run.validate_file_versions(vr)
    assert "does not have any templates" in str(e)

    # Test templates with no keys
    vr = ValidationRunFactory(data_review=data_review_with_files)
    mocker.patch(
        "creator.ingest_runs.tasks.validation_run.generate_mapper",
        return_value={}
    )
    with pytest.raises(ValueError) as e:
        validation_run.validate_file_versions(vr)
    assert "do not have keys" in str(e)


def test_validate_map_errors(db, mocker, data_review_with_files):
    """
    Test validation_run.validate_file_versions clean_and_map errors
    """
    vr = ValidationRunFactory(data_review=data_review_with_files)
    validate = validation_run.validate_file_versions

    # Test extraction error
    mock_clean_and_map = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.clean_and_map",
        side_effect=validation_run.ExtractDataError
    )
    with pytest.raises(ValueError) as e:
        validate(vr)
    assert "None of the input file formats" in str(e)

    # Test clean and map error
    mock_clean_and_map = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.clean_and_map",
        side_effect=Exception
    )
    with pytest.raises(ValueError) as e:
        validate(vr)
    assert "able to be cleaned and mapped" in str(e)

    # Test empty dfs from clean_and_map
    mock_clean_and_map = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.clean_and_map",
        return_value=pandas.DataFrame()
    )
    with pytest.raises(ValueError) as e:
        validate(vr)
    assert "None of the columns in the input" in str(e)


def test_data_validator_errors(db, mocker, data_review_with_files):
    """
    Test validation_run.validate_file_versions when data validator errors
    """
    mock_logger = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.logger",
    )
    validate = validation_run.validate_file_versions
    vr = ValidationRunFactory(data_review=data_review_with_files)

    # Test error in data validator
    mock_clean_and_map = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.clean_and_map",
        return_value=pandas.DataFrame({"A": ["B"]})
    )
    mock_validator = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.DataValidator",
    )
    mock_validator().validate.side_effect = Exception
    with pytest.raises(Exception) as e:
        validate(vr)
    mock_logger.call_count == 2


def test_build_report(db, mocker, data_review_with_files):
    """
    Test validation report building
    """
    # Validate versions
    versions = data_review_with_files.versions.all()
    vr = ValidationRunFactory(data_review=data_review_with_files)
    results = validation_run.validate_file_versions(vr)

    # Check that all versions for the review were validated
    assert results
    assert set(results["files_validated"]) == {v.kf_id for v in versions}
    report = validation_run.build_report(results)
    for v in versions:
        assert os.path.splitext(v.file_name)[0] in report


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


def test_clean_and_map(mocker):
    """
    Test the clean and map helper in the validation_run task
    """
    class MockVersion:
        def __init__(self):
            self.pk = 1
            self.file_name = "MyVersion"

    clean_and_map = validation_run.clean_and_map

    # Error extracting file content into DataFrame
    mocker.patch(
        "creator.ingest_runs.tasks.validation_run.extract_data",
        side_effect=Exception,
    )
    with pytest.raises(validation_run.ExtractDataError) as e:
        clean_and_map(MockVersion(), {})

    # Success
    mapper = {"ColA": "CONCEPT.A"}
    df = pandas.DataFrame(
        {
            "ColA": ["A"],
            "ColB": ["B"],
        }
    )
    mock_extract_data = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.extract_data",
        return_value=df
    )
    mapped_df = clean_and_map(MockVersion(), mapper)
    assert set(mapped_df.columns.tolist()) == {"CONCEPT.A"}


def test_generate_mapper(db, mocker):
    """
    Test validation_run.generate_mapper
    """
    class MockTemplate:
        def __init__(self, fields):
            self.field_definitions = {"fields": fields}
    fields = [
        {"key": f"key{i}", "label": f"label{i}"}
        for i in range(2)
    ]
    template_version = MockTemplate(fields)
    tvs = [template_version]

    # Test normal case
    mapper = validation_run.generate_mapper(tvs)
    assert mapper
    assert set(mapper.keys()) == {"key0", "key1", "label0", "label1"}

    # Test case with multiple template cols that map to same template key
    mock_logger = mocker.patch(
        "creator.ingest_runs.tasks.validation_run.logger",
    )
    new_field = fields[0].copy()
    new_field["label"] = "Column A"
    tvs[0].field_definitions["fields"].append(new_field)
    mapper = validation_run.generate_mapper(tvs)
    assert mapper
    assert mock_logger.warning.call_count == 1


def test_map_column():
    """
    Test validation_run.map_column
    """
    in_col = "  foo "
    mapper = {"foo": "bar"}
    out = validation_run.map_column(in_col, mapper)
    assert out == "bar"

    in_col = " foobar"
    out = validation_run.map_column(in_col, mapper)
    assert out is None


def test_extract_config_path(db, mocker, data_review, file_version):
    """
    Test Version.extract_config_path property
    """
    # Happy case - version has an extract config
    fv = file_version("PDA", study=data_review.study)
    assert fv.extract_config_path

    # Version file_type has no extract config
    fv.root_file.file_type = "OTH"
    assert not fv.extract_config_path

    # Version has no root_file
    fv.root_file = None
    assert not fv.extract_config_path
