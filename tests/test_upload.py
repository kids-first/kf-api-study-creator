import pytest
import json
from creator.studies.factories import StudyFactory, BatchFactory


def test_upload():
    assert True


def test_upload_query(client, db):
    StudyFactory.create_batch(1)
    batches = BatchFactory.create_batch(2)
    query = '''
        mutation ($file: Upload!, $batchId: Int!) {
          createFile(file: $file, batchId: $batchId) {
            success
          }
        }
    '''
    with open('tests/data/manifest.txt') as f:
        data = {
            'operations': json.dumps({
                'query': query.strip(),
                'variables': {
                    'file': None,
                    'batchId': batches[-1].id
                },
            }),
            'file': f,
            'map': json.dumps({
                'file': ['variables.file'],
            }),
        }
        resp = client.post('/graphql', data=data)
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' not in resp.json()
    assert resp.json() == {'data': {'createFile': {'success': True}}}
    assert batches[-1].files.count() == 1


def test_batch_not_exist(client, db):
    query = '''
        mutation ($file: Upload!, $batchId: Int!) {
          createFile(file: $file, batchId: $batchId) {
            success
          }
        }
    '''
    with open('tests/data/manifest.txt') as f:
        data = {
            'operations': json.dumps({
                'query': query.strip(),
                'variables': {
                    'file': None,
                    'batchId': 10
                },
            }),
            'file': f,
            'map': json.dumps({
                'file': ['variables.file'],
            }),
        }
        resp = client.post('/graphql', data=data)
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' in resp.json()
    expected = 'Batch matching query does not exist.'
    assert resp.json()['errors'][0]['message'] == expected
