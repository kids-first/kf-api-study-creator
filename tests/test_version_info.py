import os
import pytest
import subprocess


def test_version_info():
    from creator import version_info

    assert version_info.VERSION
    assert versino_info.COMMIT


def test_version_info(mocker):
    patch = mocker.patch("subprocess.check_output")
    patch.side_effect = subprocess.CalledProcessError("abc", 123)

    from creator import version_info

    if not os.environ.get("CI") and not os.environ.get("JOB_NAME"):
        assert version_info.VERSION == "LOCAL"
        assert version_info.COMMIT == "-"
