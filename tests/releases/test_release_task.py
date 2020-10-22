import requests
import pytest
from creator.releases.factories import ReleaseTaskFactory


@pytest.mark.parametrize("action", ["publish"])
def test_send_action(db, mocker, action):
    release_task = ReleaseTaskFactory()

    mock_header = mocker.patch("creator.releases.models.service_headers")
    mock_header.return_value = {}

    class Resp:
        def json(self):
            return {
                "state": "publishing",
                "task_id": release_task.kf_id,
                "release_id": release_task.release.kf_id,
            }

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.releases.models.requests.post")
    mock.return_value = Resp()

    release_task._send_action(action)

    assert mock.call_count == 1
    assert mock_header.call_count == 1

    mock.assert_called_with(
        f"{release_task.release_service.url}/tasks",
        headers={},
        json={
            "action": "publish",
            "task_id": release_task.kf_id,
            "release_id": release_task.release.kf_id,
        },
        timeout=30,
    )


def test_http_error(db, mocker):
    """
    Test that request that error are caught.
    """
    release_task = ReleaseTaskFactory()

    mock_header = mocker.patch("creator.releases.models.service_headers")
    mock = mocker.patch("creator.releases.models.requests.post")

    mock.side_effect = requests.exceptions.RequestException()

    with pytest.raises(requests.exceptions.RequestException):
        release_task._send_action("publish")

    assert mock.call_count == 1


def test_incorrect_task_id(db, mocker):
    """
    Test that state is not accepted if the returned task id does not
    match.
    """
    mock_header = mocker.patch("creator.releases.models.service_headers")

    release_task = ReleaseTaskFactory(state="staged")

    class Resp:
        def json(self):
            return {
                "state": "publishing",
                "task_id": "TA_00000000",
                "release_id": release_task.release.kf_id,
            }

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.releases.models.requests.post")
    mock.return_value = Resp()

    with pytest.raises(ValueError):
        release_task.publish()

    assert mock.call_count == 1
    assert release_task.state == "staged"


def test_incorrect_release_id(db, mocker):
    """
    Test that state is not accepted if the returned release id does not
    match.
    """
    mock_header = mocker.patch("creator.releases.models.service_headers")

    release_task = ReleaseTaskFactory(state="staged")

    class Resp:
        def json(self):
            return {
                "state": "publishing",
                "task_id": release_task.kf_id,
                "release_id": "RE_00000000",
            }

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.releases.models.requests.post")
    mock.return_value = Resp()

    with pytest.raises(ValueError):
        release_task.publish()

    assert mock.call_count == 1
    assert release_task.state == "staged"


def test_publish(db, mocker):
    """
    Test that publishing puts the task into the correct state.
    """
    release_task = ReleaseTaskFactory(state="staged")

    mock = mocker.patch("creator.releases.models.ReleaseTask._send_action")
    mock.return_value = {
        "state": "publishing",
        "task_id": release_task.kf_id,
        "release_id": release_task.release.kf_id,
    }

    release_task.publish()

    assert mock.call_count == 1
    assert release_task.state == "publishing"
