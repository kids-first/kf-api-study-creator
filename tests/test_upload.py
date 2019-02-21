import pytest
from creator.schema import schema

def test_upload():
    assert True

def test_study_query(client, db):
    query = '''
        {
          allStudies {
            edges {
              node {
                id
              }
            }
          }
        }
    '''
    query_data = {
        "query": query.strip()
    }
    resp = client.post('/graphql', data=query_data, content_type='application/json')
    assert resp.status_code == 200
    assert 'data' in resp.json()
