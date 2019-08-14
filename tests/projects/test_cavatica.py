import pytest
import pytz
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import setup_cavatica, create_project
from creator.studies.models import Study
from creator.projects.models import Project


@pytest.fixture
def mock_create_project(mocker):
    """ Mocks out create project functions """
    create_project = mocker.patch("creator.projects.cavatica.create_project")
    return create_project


@pytest.fixture
def mock_cavatica_api(mocker):
    """ Mocks out api for creating Cavatica project functions """

    @dataclass
    class CavaticaProject:
        id: str = "author/test"
        name: str = "Test name"
        description: str = "Test description"
        href: str = "test_url"
        created_by: str = "author"
        created_on: datetime = datetime.now(pytz.utc)
        modified_on: datetime = datetime.now(pytz.utc)
        save: Callable = MagicMock()

    sbg = mocker.patch("creator.projects.cavatica.sbg")

    # Project subresource of the sbg api
    ProjectMock = MagicMock()
    ProjectMock.create.return_value = CavaticaProject()

    Api = MagicMock()
    Api().projects = ProjectMock

    sbg.Api = Api

    return sbg


def test_correct_projects(db, mock_create_project):
    study = Study(kf_id="SD_00000000", name="test")
    study.save()

    setup_cavatica(study)

    assert mock_create_project.call_count == 3

    mock_create_project.assert_any_call(study, "DEL")
    mock_create_project.assert_any_call(study, "HAR", "bwa-mem")
    mock_create_project.assert_any_call(study, "HAR", "gatk-haplotypecaller")


def test_create_delivery_projects(db, mock_cavatica_api):
    study = Study(kf_id="SD_00000000", name="test")
    study.save()

    create_project(study, "DEL")

    # Checking if the api is constructed with the correct settings
    mock_cavatica_api.Api.assert_called_with(
        url="https://cavatica-api.sbgenomics.com/v2", token=None
    )
    mock_cavatica_api.Api().projects.create.assert_any_call(name=study.kf_id)
    mock_cavatica_api.Api().projects.save().call_count == 1

    assert Project.objects.count() == 1
    assert Project.objects.first().study == study
    assert Project.objects.first().workflow_type is None

    cavatica_project = mock_cavatica_api.Api().projects.create.return_value
    project = Project.objects.first()

    # Check if the fields are copied correctly
    assert project.url == cavatica_project.href
    assert project.project_id == cavatica_project.id

    for field in [
        "name",
        "description",
        "created_by",
        "created_on",
        "modified_on",
    ]:
        assert getattr(cavatica_project, field) == getattr(project, field)


def test_create_harmonization_projects(db, mock_cavatica_api):
    study = Study(kf_id="SD_00000000", name="test")
    study.save()

    create_project(study, "HAR", "bwa-mem")

    mock_cavatica_api.Api().projects.create.assert_any_call(
        name=study.kf_id + "-bwa-mem"
    )
    assert Project.objects.count() == 1
    assert Project.objects.first().workflow_type == "bwa-mem"
