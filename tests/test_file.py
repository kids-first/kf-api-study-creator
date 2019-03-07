import pytest
from creator.studies.factories import StudyFactory
from creator.files.models import File


def test_get_file_by_id(db, admin_client, user_client, prep_file):
    """
    Test that files cannot be retrieved by id by a user that does not belong
    to that file's study
    """
    _, file_id, _ = prep_file()

    # Get a file's relay id
    query = f'{{fileByKfId(kfId: "{file_id}") {{ id }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert 'id' in resp.json()['data']['fileByKfId']
    node_id = resp.json()['data']['fileByKfId']['id']

    # Get the study again using the study() query
    query = f'{{file(id: "{node_id}") {{ kfId }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['file']['kfId'] == file_id

    # Make sure the same query returns no node for a normal user
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['file'] is None


def test_get_file_by_kf_id(db, admin_client, prep_file):
    """
    Test that studies may be retrieved by kfId
    """
    _, file_id, _ = prep_file()

    # Test that a study may be retreived by kf_id
    query = f'{{fileByKfId(kfId: "{file_id}") {{ id name }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'fileByKfId' in resp.json()['data']
    assert 'name' in resp.json()['data']['fileByKfId']


def test_user_get_file_by_kf_id(db, user_client, prep_file):
    """
    Test that normal user can only get files in studies they belong to
    """
    _, file1_id, _ = prep_file()
    _, file2_id, _ = prep_file(authed=True)

    # Test that a study may be retreived by kf_id
    query = f'{{fileByKfId(kfId: "{file2_id}") {{ id name }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'name' in resp.json()['data']['fileByKfId']

    # Test that a study that the user does not belong to cannot be retrieved
    query = f'{{fileByKfId(kfId: "{file1_id}") {{ id name }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'fileByKfId' in resp.json()['data']
