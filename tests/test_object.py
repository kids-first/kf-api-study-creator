import pytest
from creator.studies.factories import StudyFactory


def test_get_object_by_id(db, admin_client, user_client, prep_file):
    """
    Test that files cannot be retrieved by id by a user that does not belong
    to that file's study
    """
    _, _, version_id = prep_file()

    # Get a version's relay id
    query = f'{{versionByKfId(kfId: "{version_id}") {{ id }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert 'id' in resp.json()['data']['versionByKfId']
    node_id = resp.json()['data']['versionByKfId']['id']

    # Get the study again using the study() query
    query = f'{{version(id: "{node_id}") {{ kfId }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['version']['kfId'] == version_id

    # Make sure the same query returns no node for a normal user
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['version'] is None


def test_get_version_by_kf_id(db, admin_client, prep_file):
    """
    Test that studies may be retrieved by kfId
    """
    _, _, version_id = prep_file()

    # Test that a study may be retreived by kf_id
    query = f'{{versionByKfId(kfId: "{version_id}") {{ id size }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'versionByKfId' in resp.json()['data']
    assert 'size' in resp.json()['data']['versionByKfId']


def test_user_get_version_by_kf_id(db, user_client, prep_file):
    """
    Test that normal user can only get versions in studies they belong to
    """
    _, _, version1_id = prep_file()
    _, _, version2_id = prep_file(authed=True)

    # Test that a study may be retreived by kf_id
    query = f'{{versionByKfId(kfId: "{version2_id}") {{ id size }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'size' in resp.json()['data']['versionByKfId']

    # Test that a study that the user does not belong to cannot be retrieved
    query = f'{{versionByKfId(kfId: "{version1_id}") {{ id size }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert resp.json()['data']['versionByKfId'] is None
