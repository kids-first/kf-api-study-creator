import pytest
from creator.studies.factories import StudyFactory


def test_get_study_by_id(db, admin_client, user_client):
    """
    Test that study nodes cannot be retrieved by a user who does not belong
    to that study
    """
    studies = StudyFactory.create_batch(5)

    # Get a study's relay id
    study_id = studies[0].kf_id
    query = f'{{studyByKfId(kfId: "{study_id}") {{ id }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert 'id' in resp.json()['data']['studyByKfId']
    node_id = resp.json()['data']['studyByKfId']['id']

    # Get the study again using the study() query
    query = f'{{study(id: "{node_id}") {{ kfId }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['study']['kfId'] == study_id

    # Make sure the same query returns no node for a normal user
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.json()['data']['study'] is None


def test_get_study_by_kf_id(db, admin_client):
    """
    Test that studies may be retrieved by kfId
    """
    studies = StudyFactory.create_batch(5)

    # Test that a study may be retreived by kf_id
    study_id = studies[0].kf_id
    query = f'{{studyByKfId(kfId: "{study_id}") {{ id name }} }}'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'studyByKfId' in resp.json()['data']
    assert 'name' in resp.json()['data']['studyByKfId']


def test_user_get_study_by_kf_id(db, user_client):
    """
    Test that normal user can only get study that they own
    """
    studies = StudyFactory.create_batch(5)
    studies[0].kf_id = 'SD_00000000'
    studies[0].save()

    # Test that a study may be retreived by kf_id
    study_id = studies[0].kf_id
    query = f'{{studyByKfId(kfId: "{study_id}") {{ id name }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'name' in resp.json()['data']['studyByKfId']

    # Test that a study that the user does not belong to cannot be retrieved
    study_id = studies[1].kf_id
    query = f'{{studyByKfId(kfId: "{study_id}") {{ id name }} }}'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'studyByKfId' in resp.json()['data']
