import pytest
import pytz
import sevenbridges as sbg
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import (
    setup_cavatica,
    create_project,
    copy_users,
)
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
    mock_create_project.assert_any_call(study, "HAR", "bwa_mem")
    mock_create_project.assert_any_call(study, "HAR", "gatk_haplotypecaller")


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

    create_project(study, "HAR", "bwa_mem")

    mock_cavatica_api.Api().projects.create.assert_any_call(
        name=study.kf_id + "-bwa_mem"
    )
    assert Project.objects.count() == 1
    assert Project.objects.first().workflow_type == "bwa_mem"


def test_user_copy_is_called(db, mocker, mock_cavatica_api):
    """
    Test that creating a new project will copy users
    """
    study = Study(kf_id="SD_00000000", name="test")
    study.save()
    copy_users = mocker.patch("creator.projects.cavatica.copy_users")

    create_project(study, "HAR", "bwa_mem")

    assert copy_users.call_count == 1
    call = copy_users.call_args_list[0]


def test_user_copy(db, settings, mocker, mock_cavatica_api):
    """
    Test that an analysis project is setup with users from the template
    repository.
    """
    settings.CAVATICA_USER_ACCESS_PROJECT = "test/user-access"
    # Mock the new project
    new_project = sbg.models.project.Project(
        id="test/my-project", name="Test project"
    )
    # Mock the user  access project and call to get it
    project = sbg.models.project.Project(
        id="test/user-access", name="User access project"
    )
    mock_cavatica_api.Api().projects.get.return_value = project
    # Mock a user inside the user access project
    user = sbg.models.member.Member(
        username="test",
        permissions={
            "write": True,
            "read": True,
            "copy": True,
            "execute": False,
            "admin": False,
        },
    )
    project.get_members = MagicMock()
    project.get_members.return_value = [user]
    new_project.add_member = MagicMock()
    new_project.add_member.return_value = user

    copy_users(mock_cavatica_api.Api(), new_project)

    mock_cavatica_api.Api().projects.get.assert_called_with(
        id=settings.CAVATICA_USER_ACCESS_PROJECT
    )
    assert project.get_members.call_count == 1
    new_project.add_member.assert_called_with(
        "test", permissions=user.permissions
    )
