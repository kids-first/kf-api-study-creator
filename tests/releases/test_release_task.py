import requests
import pytest
from creator.releases.factories import ReleaseTaskFactory


@pytest.mark.parametrize("action", ["publish"])
def test_send_action(db, mocker, action):
    release_task = ReleaseTaskFactory()

    mock_header = mocker.patch("creator.releases.models.service_headers")
    mock_header.return_value = {}

    mock = mocker.patch("creator.releases.models.requests.post")

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
