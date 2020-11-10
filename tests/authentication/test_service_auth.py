import requests
import pytest
from django.conf import settings
from django.core.cache import cache
from creator.authentication import service_headers, get_service_token


def test_service_headers_from_cache(db, mocker):
    """
    Test that headers are retrieved from the cache when they exist
    """

    cache.set(settings.CACHE_AUTH0_SERVICE_KEY, "ABC")

    headers = service_headers()
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer ABC"

    cache.delete(settings.CACHE_AUTH0_SERVICE_KEY)


def test_service_headers(db, mocker):
    """
    Test that a new token is fetched if it is not in the cache
    """
    mock_token = mocker.patch("creator.authentication.get_service_token")
    mock_token.return_value = "ABC"

    headers = service_headers()
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer ABC"

    assert cache.get(settings.CACHE_AUTH0_SERVICE_KEY) == "ABC"
    cache.delete(settings.CACHE_AUTH0_SERVICE_KEY)


def test_new_service_token(db, mocker):
    """
    Test that Auth0 is called for a new token
    """

    class Resp:
        def json(self):
            return {"access_token": "ABC"}

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.authentication.requests.post")
    mock.return_value = Resp()

    assert get_service_token() == "ABC"


def test_new_service_token_malformed_resp(db, mocker):
    """
    Test the case that Auth0 returns json without an access key
    """

    class Resp:
        def json(self):
            return {"notvalid": None}

        def content(self):
            return "blah"

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.authentication.requests.post")
    mock.return_value = Resp()

    assert get_service_token() is None
    assert mock.call_count == 1


def test_new_service_token_exception(db, mocker):
    """
    Test that no token is returned if there is a problem with the request
    """
    settings.AUTH0_CLIENT = "123"
    settings.AUTH0_SECRET = "abc"
    settings.AUTH0_SERVICE_AUD = "https://my-service.auth0.com"

    mock = mocker.patch("creator.authentication.requests.post")
    mock.side_effect = requests.exceptions.RequestException("error")

    assert get_service_token() is None
    assert mock.call_count == 1
