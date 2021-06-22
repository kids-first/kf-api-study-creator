import pytest
import pytz
from datetime import datetime
import sevenbridges as sbg
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from creator.projects.cavatica import (
    setup_cavatica,
    create_project,
    copy_users,
    import_volume_files,
    NotLinkedError,
    VolumeNotFound,
)

from creator.studies.factories import StudyFactory
from creator.projects.models import Project
from creator.projects.factories import ProjectFactory


@pytest.fixture
def mock_create_project(mocker):
    """ Mocks out create project functions """
    create_project = mocker.patch("creator.projects.cavatica.create_project")
    return create_project


def test_correct_projects_no_default(db, mock_create_project):
    study = StudyFactory(kf_id="SD_00000000", name="test")
    study.save()

    setup_cavatica(study)

    assert mock_create_project.call_count == 1
    mock_create_project.assert_any_call(study, "DEL", user=None)


def test_correct_projects_with_default(db, settings, mock_create_project):
    settings.CAVATICA_DEFAULT_WORKFLOWS = ["bwa_mem", "gatk_haplotypecaller"]
    study = StudyFactory(kf_id="SD_00000000", name="test")
    study.save()

    setup_cavatica(study)

    assert mock_create_project.call_count == 3

    mock_create_project.assert_any_call(study, "DEL", user=None)
    mock_create_project.assert_any_call(study, "HAR", "bwa_mem", user=None)
    mock_create_project.assert_any_call(
        study, "HAR", "gatk_haplotypecaller", user=None
    )


def test_create_delivery_projects(db, mock_cavatica_api):
    study = StudyFactory(kf_id="SD_00000000", name="test")
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
    study = StudyFactory(kf_id="SD_00000000", name="test")
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
    study = StudyFactory(kf_id="SD_00000000", name="test")
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


def test_import_volume_files_not_linked(db, mock_cavatica_api):
    cavatica_project = mock_cavatica_api.Api().projects.create.return_value

    project = ProjectFactory()

    with pytest.raises(NotLinkedError):
        import_volume_files(project)


def test_import_volume_files_no_volume(db, settings, mock_cavatica_api):
    settings.CAVATICA_DELIVERY_ACCOUNT = "test-acct"
    cavatica_project = mock_cavatica_api.Api().projects.create.return_value

    study = StudyFactory()
    project = ProjectFactory(study=study)

    mock_cavatica_api.Api().volumes.get.return_value = None

    with pytest.raises(VolumeNotFound):
        import_volume_files(project)


def test_import_volume_files_could_not_get_volume(
    db, settings, mock_cavatica_api
):
    settings.CAVATICA_DELIVERY_ACCOUNT = "test-acct"
    cavatica_project = mock_cavatica_api.Api().projects.create.return_value

    study = StudyFactory()
    project = ProjectFactory(study=study)

    mock_cavatica_api.Api().volumes.get.side_effect = sbg.errors.NotFound

    with pytest.raises(VolumeNotFound):
        import_volume_files(project)


def test_import_volume_files_folder_exists(db, settings, mock_cavatica_api):
    settings.CAVATICA_DELIVERY_ACCOUNT = "test-acct"
    cavatica_project = mock_cavatica_api.Api().projects.create.return_value

    class Folder:
        def __init__(self, name):
            self.name = name

    mock_cavatica_api.Api().files.create_folder.side_effect = (
        sbg.errors.Conflict()
    )
    folder_name = f"{datetime.now().strftime('%Y-%m-%d')}-kf-data-delivery"
    mock_cavatica_api.Api().files.query.return_value = [
        Folder("abc"),
        Folder("123"),
        Folder(folder_name),
    ]

    study = StudyFactory()
    project = ProjectFactory(study=study)

    import_volume_files(project)

    assert mock_cavatica_api.Api().files.query.call_count == 1
    mock_cavatica_api.Api().files.query.assert_called_with(
        project=project.project_id
    )


def test_import_volume_files(db, settings, mock_cavatica_api):
    settings.CAVATICA_DELIVERY_ACCOUNT = "test-acct"
    cavatica_project = mock_cavatica_api.Api().projects.create.return_value

    study = StudyFactory()
    project = ProjectFactory(study=study)

    class VolumeObject:
        def __init__(self, path):
            self.location = path

    class PrefixObj:
        def __init__(self, prefix):
            self.prefix = prefix

    class PrefixList:
        @property
        def prefixes(self):
            return [
                PrefixObj("source/uploads"),
                PrefixObj("source/bams"),
                PrefixObj("source/test"),
            ]

        def __iter__(self):
            return iter([VolumeObject("123"), VolumeObject("abc")])

    class Volume:
        def __init__(self):
            self.id = f"test-acct/{study.kf_id}"

        def list(self, prefix):
            return PrefixList()

    mock_cavatica_api.Api().volumes.get.return_value = Volume()

    import_volume_files(project)

    mock_cavatica_api.Api().volumes.get.assert_called_with(
        f"test-acct/{study.kf_id}"
    )

    # two valid subdirectories and two objects in the source directory = 4
    assert mock_cavatica_api.Api().imports.bulk_submit.call_count == 1
    assert (
        len(mock_cavatica_api.Api().imports.bulk_submit.call_args_list[0]) == 2
    )
