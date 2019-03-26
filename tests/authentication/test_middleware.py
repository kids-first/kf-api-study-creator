import json
import jwt
import pytest
import mock
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from creator.studies.models import Study


@pytest.fixture(scope='session', autouse=True)
def ego_key_mock():
    """
    This overrides the ego_key_mock that is applied to all tests
    """
    pass


@pytest.mark.no_mocks
def test_ego_middleware(db, client, token):
    """
    Test that ego middleware will call ego to get a public_key

    Mock out the get request, returning a public key and assert that it has
    been called once.
    """
    key = cache.set(settings.CACHE_EGO_KEY, None)

    middleware = 'creator.middleware'
    ego_middleware = f'{middleware}.EgoJWTAuthenticationMiddleware'
    auth0_middleware = f'{middleware}.Auth0AuthenticationMiddleware'

    req_patch = mock.patch(f'{middleware}.requests.get')
    # We'll mock out the response of the get request to allow request to pass
    req_mock = req_patch.start()
    with open('tests/keys/public_key.pem', 'rb') as f:
        class Resp:
            content = f.read()
        req_mock.return_value = Resp()

    auth0_patch = mock.patch(f'{auth0_middleware}.get_jwt_user')
    auth0_mock = auth0_patch.start()
    auth0_mock.return_value = AnonymousUser()

    study = Study(kf_id='SD_ME0WME0W')
    study.save()

    # Send a test query
    q = '{ allStudies { edges { node { name } } } }'
    token = token(groups=[], roles=['ADMIN'])
    resp = client.post(
        '/graphql',
        data={'query': q},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    assert 'allStudies' in resp.json()['data']
    assert len(resp.json()['data']['allStudies']['edges']) == 1

    req_mock.assert_called_with(f'{settings.EGO_API}/oauth/token/public_key',
                                timeout=10)
    req_patch.stop()
    auth0_patch.stop()


@pytest.mark.no_mocks
def test_auth0_middleware(db, client, token):
    """
    Test that auth0 middleware will call ego to get a public_key

    Mock out ego's response with a token invalid error, then mock out the get
    request to auth0, returning a public key and assert that it has been called
    once.
    """
    key = cache.set(settings.CACHE_AUTH0_KEY, None)

    middleware = 'creator.middleware'
    ego_middleware = f'{middleware}.EgoJWTAuthenticationMiddleware'
    auth0_middleware = '{middleware}.Auth0AuthenticationMiddleware'

    req_patch = mock.patch(f'{middleware}.requests.get')
    req_mock = req_patch.start()
    with open('tests/keys/jwks.json', 'rb') as f:
        req_mock().json.return_value = json.load(f)
    # Ego will responed with un-authed user when it can't validate token
    ego_patch = mock.patch(f'{ego_middleware}.get_jwt_user')
    ego_mock = ego_patch.start()
    ego_mock.return_value = AnonymousUser()

    study = Study(kf_id='SD_ME0WME0W')
    study.save()

    # Send a test query
    q = '{ allStudies { edges { node { name } } } }'
    token = token(groups=[], roles=['ADMIN'], iss='auth0')
    resp = client.post(
        '/graphql',
        data={'query': q},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    assert 'allStudies' in resp.json()['data']
    assert len(resp.json()['data']['allStudies']['edges']) == 1

    # There should be requests made for keys on both auth services
    assert req_mock.call_count == 2
    req_mock.assert_called_with(settings.AUTH0_JWKS, timeout=10)

    ego_patch.stop()
    req_patch.stop()
