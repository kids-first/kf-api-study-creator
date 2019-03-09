import jwt
import pytest
import mock


def test_corrupt_jwt(db, client):
    """
    Test that a poorly formatted token fails validation
    """
    q = '{ allStudies { edges { node { name } } } }'
    resp = client.post(
        '/graphql',
        data={'query': q},
        content_type='application/json',
        HTTP_AUTHORIZATION='Bearer undefined'
    )
    assert 'errors' in resp.json()
    assert 'Not enough segments' in resp.json()['errors'][0]['message']


def test_invalid_jwt(db, client, token):
    """
    Test that an improperly signed token fails validation
    """
    decoded = jwt.decode(token(), verify=False)
    with open('tests/keys/other_private_key.pem') as f:
        key = f.read()
    encoded = jwt.encode(decoded, key, algorithm='RS256').decode('utf-8')
    q = '{ allStudies { edges { node { name } } } }'

    resp = client.post(
        '/graphql',
        data={'query': q},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {str(encoded)}'
    )
    assert 'errors' in resp.json()
    assert 'Signature verification fail' in resp.json()['errors'][0]['message']
