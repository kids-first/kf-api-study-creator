import jwt
import pytest
import mock
from django.conf import settings


@pytest.fixture(scope='session', autouse=True)
def ego_key_mock():
    """
    This overrides the ego_key_mock that is applied to all tests
    """
    pass


@pytest.mark.no_key_mocks
def test_ego_middleware(db, client, token):
    """
    Test that ego middleware will call ego to get a public_key

    Mock out the get request, returning a public key and assert that it has
    been called once.
    """
    middleware = 'creator.middleware'
    with mock.patch(f'{middleware}.requests.get') as req:
        # We'll mock out the response of the get request to allow request
        # to pass
        with open('tests/keys/public_key.pem', 'rb') as f:
            req.return_value = f.read()

        # Send a test query
        q = '{ allStudies { edges { node { name } } } }'
        token = token(groups=[], roles=['ADMIN'])
        resp = client.post(
            '/graphql',
            data={'query': q},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        # Success should have passed
        assert 'allStudies' in resp.json()['data']

        # The middleware should have sent one get request to ego
        assert req.call_count == 1
        req.assert_called_with(f'{settings.EGO_API}/oauth/token/public_key',
                               timeout=10)
