import pytest
from creator.studies.factories import StudyFactory
from creator.studies.models import Study


def test_schema_query(client, db):
    query = '''
        {__schema {
          types {
            name
            description
          }
        }}
    '''
    query_data = {
        "query": query.strip()
    }
    resp = client.post(
        '/graphql',
        data=query_data,
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert '__schema' in resp.json()['data']


def test_unauthed_study_query(client, db):
    """
    Queries made with no authentication should return no studies
    """
    studies = StudyFactory.create_batch(5)
    query = '{ allStudies { edges { node { name } } } }'
    resp = client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'allStudies' in resp.json()['data']
    assert len(resp.json()['data']['allStudies']['edges']) == 0


def test_my_studies_query(user_client, db):
    """
    Test that only studies belonging to the user are returned
    """
    studies = StudyFactory.create_batch(5)
    # Make the user's study
    study = Study(kf_id='SD_00000000', external_id='Test')
    study.save()

    query = '{ allStudies { edges { node { name } } } }'
    resp = user_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'allStudies' in resp.json()['data']
    assert len(resp.json()['data']['allStudies']['edges']) == 1


def test_admin_studies_query(admin_client, db):
    """
    Test that only studies belonging to the user are returned
    """
    studies = StudyFactory.create_batch(5)

    query = '{ allStudies { edges { node { name } } } }'
    resp = admin_client.post(
        '/graphql',
        data={'query': query},
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'allStudies' in resp.json()['data']
    assert len(resp.json()['data']['allStudies']['edges']) == 5
