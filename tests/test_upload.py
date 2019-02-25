import pytest
import json
from creator.studies.factories import StudyFactory


def test_upload():
    assert True


def test_upload_query(client, db):
    studies = StudyFactory.create_batch(2)
    query = '''
        mutation ($file: Upload!, $studyId: String!) {
          createFile(file: $file, studyId: $studyId) {
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
                    'studyId': studies[-1].kf_id
                },
            }),
            'file': f,
            'map': json.dumps({
                'file': ['variables.file'],
            }),
        }
        resp = client.post('/graphql', data=data)
        print(resp.json())
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' not in resp.json()
    assert resp.json() == {'data': {'createFile': {'success': True}}}
    assert studies[-1].files.count() == 1


def test_study_not_exist(client, db):
    query = '''
        mutation ($file: Upload!, $studyId: String!) {
          createFile(file: $file, studyId: $studyId) {
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
                    'studyId': 10
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
    expected = 'Study matching query does not exist.'
    assert resp.json()['errors'][0]['message'] == expected
