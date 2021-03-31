import requests
from django.core.cache import cache
from django.contrib.auth import get_user_model

from creator.middleware import Auth0AuthenticationMiddleware

User = get_user_model()


def test_new_auth0_user(client, token, db):
    """
    Test that a user is saved in the database upon first request with an Auth0
    token.
    """
    # Create an Auth0 token
    token = token(["ADMIN"], ["SD_ME0WME0W"])

    assert User.objects.count() == 0

    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": query},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert User.objects.count() == 1
    user = User.objects.first()
    # Groups and roles should be empty, despite token containing them
    assert user.username == "bobby"
    assert user.email == "bobbytables@example.com"
    last_login = user.last_login

    resp = client.post(
        "/graphql",
        data={"query": query},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert User.objects.count() == 1
    user = User.objects.first()
    assert user.last_login > last_login


def test_new_service_user(db, client, service_token, mocker):
    """
    Test that a request coming from a service token correctly registers a
    new service user.
    """
    token = service_token()

    class MockResp:
        def json(self):
            return {
                "name": "Release Coordinator",
                "logo_uri": "https://example.com",
            }

        def raise_for_status(self):
            pass

    mock_req = mocker.patch("creator.middleware.requests.get")
    mock_req.return_value = MockResp()

    query = "{ allStudies { edges { node { name } } } }"
    resp = client.post(
        "/graphql",
        data={"query": query},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert User.objects.count() == 1
    user = User.objects.first()

    assert "@clients" in user.sub
    assert user.groups.filter(name="Services").exists()


def test_get_app_info(db, mocker, settings):
    """
    Test that app info is correctly requested from Auth0
    """
    # Inject a fake service token into the cache for use with the Auth0 API
    cache.set(settings.CACHE_AUTH0_SERVICE_KEY, "abc")

    class MockResp:
        def json(self):
            return {
                "name": "Release Coordinator",
                "logo_uri": "https://example.com",
            }

        def raise_for_status(self):
            pass

    mock_req = mocker.patch("creator.middleware.requests.get")
    mock_req.return_value = MockResp()

    profile = Auth0AuthenticationMiddleware._get_app_info("mysub@client")

    assert profile["nickname"] == "Release Coordinator"
    assert profile["given_name"] == "Release Coordinator"
    assert profile["family_name"] == "Service"
    assert profile["picture"] == "https://example.com"


def test_get_app_info_bad_status(db, mocker, settings):
    """
    Test that None is returned if there is a problem getting app info
    """
    # Inject a fake service token into the cache for use with the Auth0 API
    cache.set(settings.CACHE_AUTH0_SERVICE_KEY, "abc")

    mock_req = mocker.patch("creator.middleware.requests.get")
    mock_req.side_effect = requests.exceptions.HTTPError("404!")

    profile = Auth0AuthenticationMiddleware._get_app_info("mysub@client")

    assert profile is None
