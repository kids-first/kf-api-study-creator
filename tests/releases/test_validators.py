import pytest
import requests.exceptions
from django.core.exceptions import ValidationError
from creator.releases.validators import validate_endpoint


def test_validate_endpoint_invalid_url():
    with pytest.raises(ValidationError):
        validate_endpoint("not a url")


def test_validate_endpoint_bad_status(mocker):
    mock = mocker.patch("creator.releases.validators.requests.get")
    mock.side_effect = requests.exceptions.RequestException()

    with pytest.raises(ValidationError):
        validate_endpoint("http://valid")


def test_validate_endpoint_not_200(mocker):
    class MockResp:
        status_code = 400

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.releases.validators.requests.get")
    mock.return_value = MockResp()

    with pytest.raises(ValidationError):
        validate_endpoint("http://valid")


def test_validate_endpoint_bad_json(mocker):
    class MockResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            raise ValueError("Could not decode JSON")

    mock = mocker.patch("creator.releases.validators.requests.get")
    mock.return_value = MockResp()

    with pytest.raises(ValidationError):
        validate_endpoint("http://valid")


def test_validate_endpoint_bad_name(mocker):
    class MockResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"no name"}

    mock = mocker.patch("creator.releases.validators.requests.get")
    mock.return_value = MockResp()

    with pytest.raises(ValidationError):
        validate_endpoint("http://valid")


def test_validate_endpoint(mocker):
    class MockResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"name": "Test Service"}

    mock = mocker.patch("creator.releases.validators.requests.get")
    mock.return_value = MockResp()

    assert validate_endpoint("http://valid") is None
