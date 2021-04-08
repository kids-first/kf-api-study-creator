import requests
import pytest
from django.conf import settings
from django.core.cache import cache
from creator.authentication import client_headers, get_token


def test_headers_from_cache(db, mocker):
    """
    Test that headers are retrieved from the cache when they exist
    """
    cache_key = "ACCESS_TOKEN:my_aud"
    cache.set(cache_key, "ABC")

    headers = client_headers("my_aud")
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer ABC"

    cache.delete(cache_key)


def test_header_cache(db, mocker):
    """
    Test that a new token is fetched if it is not in the cache
    """
    mock_token = mocker.patch("creator.authentication.get_token")
    mock_token.return_value = "ABC"

    headers = client_headers(settings.AUTH0_SERVICE_AUD)
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer ABC"

    cache_key = f"ACCESS_TOKEN:{settings.AUTH0_SERVICE_AUD}"
    assert cache.get(cache_key) == "ABC"
    cache.delete(cache_key)


def test_new_token(db, mocker):
    """
    Test that Auth0 is called for a new token
    """
    settings.AUTH0_CLIENT = "123"
    settings.AUTH0_SECRET = "abc"

    class Resp:
        def json(self):
            return {"access_token": "ABC"}

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.authentication.requests.post")
    mock.return_value = Resp()

    assert get_token("my_aud") == "ABC"
    assert mock.call_count == 1


def test_new_token_malformed_resp(db, mocker):
    """
    Test the case that Auth0 returns json without an access key
    """
    settings.AUTH0_CLIENT = "123"
    settings.AUTH0_SECRET = "abc"

    class Resp:
        def json(self):
            return {"notvalid": None}

        def content(self):
            return "blah"

        def raise_for_status(self):
            pass

    mock = mocker.patch("creator.authentication.requests.post")
    mock.return_value = Resp()

    assert get_token("my_aud") is None
    assert mock.call_count == 1


def test_new_token_exception(db, mocker):
    """
    Test that no token is returned if there is a problem with the request
    """
    settings.AUTH0_CLIENT = "123"
    settings.AUTH0_SECRET = "abc"

    mock = mocker.patch("creator.authentication.requests.post")
    mock.side_effect = requests.exceptions.RequestException("error")

    assert get_token("my_aud") is None
    assert mock.call_count == 1


def test_new_token_insuficient_config(db, mocker):
    """
    Test that no token is fetched when there is not enough config
    """
    settings.AUTH0_CLIENT = None

    mock = mocker.patch("creator.authentication.requests.post")

    assert get_token("my_aud") is None
    assert mock.call_count == 0
