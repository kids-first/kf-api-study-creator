import json
import jwt
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import management
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from creator.studies.models import Study

User = get_user_model()


@pytest.fixture(scope="session", autouse=True)
def auth0_key_mock():
    """
    Override the auth0_key_mock that mocks out requests to auth0 for keys
    """
    pass


@pytest.mark.no_mocks
def test_auth0_middleware(db, client, mocker, token):
    """
    Test that auth0 middleware will call auth0 to get a public_key
    """
    key = cache.set(settings.CACHE_AUTH0_KEY, None)

    middleware = "creator.middleware"

    req_mock = mocker.patch(f"{middleware}.requests.get")
    with open("tests/keys/jwks.json", "rb") as f:
        req_mock().json.return_value = json.load(f)

    study = Study(kf_id="SD_ME0WME0W")
    study.save()
    assert User.objects.count() == 0

    # Send a test query
    q = "{ allStudies { edges { node { name } } } }"
    token = token(groups=[], roles=["ADMIN"])
    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert User.objects.count() == 1
    assert User.objects.first().groups.first().name == "Administrators"

    # There should be requests made for keys on both auth services
    assert req_mock.call_count == 2
    req_mock.assert_called_with(settings.AUTH0_JWKS, timeout=10)


@pytest.mark.no_mocks
def test_auth0_no_sub(db, client, mocker, token):
    """
    Test that if no sub is included in the token, the user will be authed
    as an AnonymousUser.
    """
    key = cache.set(settings.CACHE_AUTH0_KEY, None)

    middleware = "creator.middleware"

    req_mock = mocker.patch(f"{middleware}.requests.get")
    with open("tests/keys/jwks.json", "rb") as f:
        req_mock().json.return_value = json.load(f)

    token = token(sub=None)

    # Send a test query
    q = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert User.objects.count() == 0


@pytest.mark.no_mocks
def test_auth0_no_profile(db, client, mocker, token):
    """
    Test that a user does not get authenticated when their profile cannot
    be resolved.
    """
    key = cache.set(settings.CACHE_AUTH0_KEY, None)

    middleware = "creator.middleware"

    req_mock = mocker.patch(f"{middleware}.requests.get")
    with open("tests/keys/jwks.json", "rb") as f:
        req_mock().json.return_value = json.load(f)
    profile_mock = mocker.patch(
        f"{middleware}.Auth0AuthenticationMiddleware._get_profile"
    )
    profile_mock.return_value = None

    token = token()

    # Send a test query
    q = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert User.objects.count() == 0
    assert profile_mock.call_count == 1


@pytest.mark.no_mocks
def test_auth0_expired_token(db, client, mocker, token):
    """
    Test that user is not authenticated if the token has expired
    """
    key = cache.set(settings.CACHE_AUTH0_KEY, None)

    middleware = "creator.middleware"

    req_mock = mocker.patch(f"{middleware}.requests.get")
    with open("tests/keys/jwks.json", "rb") as f:
        req_mock().json.return_value = json.load(f)

    warn_mock = mocker.patch(f"{middleware}.logger.warning")

    study = Study(kf_id="SD_ME0WME0W")
    study.save()
    assert User.objects.count() == 0

    # Send a test query
    q = "{ allStudies { edges { node { name } } } }"
    token = token(groups=[], roles=["ADMIN"], exp=1)
    resp = client.post(
        "/graphql",
        data={"query": q},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert User.objects.count() == 0
    assert warn_mock.call_count == 1


def test_test_user(db, settings, mocker, clients):
    """
    Test that requests are authenticated as testuser in develop mode
    """
    settings.DEVELOP = True
    management.call_command("setup_test_user")

    query = "{ myProfile { username email } }"

    client = clients.get(None)

    resp = client.post(
        "/graphql", data={"query": query}, content_type="application/json"
    )
    assert resp.json()["data"]["myProfile"]["username"] == "testuser"
