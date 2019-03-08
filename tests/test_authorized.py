import pytest
from creator.studies.factories import StudyFactory


@pytest.mark.parametrize('resource', ['study', 'file', 'version'])
@pytest.mark.parametrize('user_type,expected', [
    ('admin', True),
    ('user', True),
    ('other_user', False),
    (None, False),
])
def test_get_resource_by_id(db, admin_client, user_client, client,
                            prep_file, resource, user_type, expected):
    """
    Test that resource may be retrieved by (relay) id
    - Should return resource if admin
    - Should return resource if user who is part of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    api_client = {
        'admin': admin_client,
        'user': user_client,
        'other_user': user_client,
        None: client
    }[user_type]

    # Create a file in the user's study if using 'user' type
    s_id, f_id, v_id = prep_file(authed=(user_type == 'user'))
    # Get the id of the resource we're testing for
    kf_id = {'study': s_id, 'file': f_id, 'version': v_id}[resource]

    # Get a node's relay id using admin client
    query = f'{{{resource}ByKfId(kfId: "{kf_id}") {{ id }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert 'id' in resp.json()['data'][f'{resource}ByKfId']
    node_id = resp.json()['data'][f'{resource}ByKfId']['id']

    # Now try to get node by the relay id
    query = f'{{{resource}(id: "{node_id}") {{ id }} }}'
    resp = api_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )

    assert 'errors' not in resp.json()
    # Should get back the node with id if expected, None if not
    if expected:
        assert resp.json()['data'][resource]['id'] == node_id
    else:
        assert resp.json()['data'][resource] is None


@pytest.mark.parametrize('resource', ['study', 'file', 'version'])
@pytest.mark.parametrize('user_type,expected', [
    ('admin', True),
    ('user', True),
    ('other_user', False),
    (None, False),
])
def test_get_resource_by_kf_id(db, admin_client, user_client, client,
                               prep_file, resource, user_type, expected):
    """
    Test that resource may be retrieved by kfId
    - Will return resource if admin
    - Should return resource if user who is parto of study
    - Should return None if user who is not part of study
    - Should return None if not an authenticated user
    """
    # Select client based on user type
    api_client = {
        'admin': admin_client,
        'user': user_client,
        'other_user': user_client,
        None: client
    }[user_type]

    # Create a file in the user's study if using 'user' type
    s_id, f_id, v_id = prep_file(authed=(user_type == 'user'))
    # Get the id of the resource we're testing for
    kf_id = {'study': s_id, 'file': f_id, 'version': v_id}[resource]

    # Test that a study may be retreived by kf_id
    query = f'{{{resource}ByKfId(kfId: "{kf_id}") {{ id kfId }} }}'
    resp = api_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )

    assert 'errors' not in resp.json()
    assert f'{resource}ByKfId' in resp.json()['data']
    # Will return size if authenticated, None if not
    if expected:
        assert 'kfId' in resp.json()['data'][f'{resource}ByKfId']
    else:
        assert resp.json()['data'][f'{resource}ByKfId'] is None
