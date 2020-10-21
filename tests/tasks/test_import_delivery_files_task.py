import pytest
from django.contrib.auth import get_user_model

from creator.projects.models import Project
from creator.projects.factories import ProjectFactory
from creator.events.models import Event
from creator.tasks import import_delivery_files_task

User = get_user_model()


def test_import_delivery_files_task(db, mocker):
    """
    Test that delivery file setup is done correctly
    """
    mock = mocker.patch("creator.tasks.import_volume_files")

    project = ProjectFactory()
    user = User(sub="abc", ego_roles=["USER"], ego_groups=[])
    user.save()

    import_delivery_files_task(project.project_id, user.sub)

    assert mock.call_count == 1
    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="IM_STR").count() == 1
    assert Event.objects.filter(event_type="IM_SUC").count() == 1


def test_import_delivery_files_task_no_project(db, mocker):
    """
    Test that task will fail if the project does not exist
    """
    mock = mocker.patch("creator.tasks.import_volume_files")

    user = User(sub="abc", ego_roles=["USER"], ego_groups=[])
    user.save()

    with pytest.raises(Project.DoesNotExist):
        import_delivery_files_task("does not exist", user.sub)

    assert mock.call_count == 0
    assert Event.objects.count() == 0


def test_import_delivery_files_task_no_user(db, mocker):
    """
    Test that task will fail if the user does not exist
    """
    mock = mocker.patch("creator.tasks.import_volume_files")

    project = ProjectFactory()
    import_delivery_files_task(project.project_id, 'test')

    assert mock.call_count == 1
    assert Event.objects.filter(event_type="IM_STR").first().user is None


def test_import_delivery_files_task_error(db, mocker):
    """
    Test that errors are logged correctly
    """
    mock = mocker.patch("creator.tasks.import_volume_files")
    mock.side_effect = Exception("error occured")

    project = ProjectFactory()
    user = User(sub="abc", ego_roles=["USER"], ego_groups=[])
    user.save()

    with pytest.raises(Exception):
        import_delivery_files_task(project.project_id, user.sub)

    assert mock.call_count == 1
    assert Event.objects.filter(event_type="IM_ERR").count() == 1
