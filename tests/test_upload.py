import os
import pytest
import json
import boto3
from moto import mock_s3

from django.conf import settings
from creator.studies.factories import StudyFactory
from creator.files.models import Object


def test_upload():
    assert True


@mock_s3
def test_upload_query_s3(client, db, tmp_uploads_s3):
    s3 = boto3.client('s3')
    studies = StudyFactory.create_batch(2)
    bucket = tmp_uploads_s3(studies[0].bucket)

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
                    'studyId': studies[0].kf_id
                },
            }),
            'file': f,
            'map': json.dumps({
                'file': ['variables.file'],
            }),
        }
        resp = client.post('/graphql', data=data)

    contents = s3.list_objects(Bucket=studies[0].bucket)['Contents']
    assert len(contents) == 1
    assert contents[0]['Key'].endswith('manifest.txt')
    assert contents[0]['Key'].startswith(settings.UPLOAD_DIR)
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' not in resp.json()
    assert resp.json() == {'data': {'createFile': {'success': True}}}
    assert studies[0].files.count() == 1
    assert studies[-1].files.count() == 0


def test_upload_query_local(client, db, tmp_uploads_local):
    studies = StudyFactory.create_batch(2)
    query = '''
        mutation ($file: Upload!, $studyId: String!) {
          createFile(file: $file, studyId: $studyId) {
            success
            file { name }
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

    obj = Object.objects.first()
    assert len(tmp_uploads_local.listdir()) == 1
    assert (tmp_uploads_local.listdir()[0]
                             .listdir()[0]
                             .strpath.endswith('manifest.txt'))
    assert obj.key.path.startswith(
            os.path.join(
                settings.UPLOAD_DIR,
                obj.root_file.study.bucket,
                'manifest'))
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' not in resp.json()
    assert resp.json() == {
        'data': {
            'createFile': {'success': True, 'file': {'name': 'manifest.txt'}}
        }
    }
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


def test_file_too_large(client, db, upload_file, settings):
    settings.FILE_MAX_SIZE = 1
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, 'manifest.txt')
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'errors' in resp.json()
    expected = 'File is too large.'
    assert resp.json()['errors'][0]['message'] == expected
