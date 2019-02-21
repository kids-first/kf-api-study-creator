import pytest
from creator.studies.factories import StudyFactory


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


def test_study_query(client, db):
    studies = StudyFactory.create_batch(5)
    query = '''
        {
          allStudies {
            edges {
              node {
                name
              }
            }
          }
        }
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
    assert 'allStudies' in resp.json()['data']
    assert 5 == len(resp.json()['data']['allStudies']['edges'])
