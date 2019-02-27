import os
import pytest
import json
import boto3
from moto import mock_s3

from creator.files.models import Object, File
from creator.studies.factories import StudyFactory


def test_download(client, db, tmp_uploads_local, upload_file):
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp1 = upload_file(study_id, 'manifest.txt')
    file1_id = File.objects.filter(name='manifest.txt').first().id
    resp2 = upload_file(study_id, 'data.csv')
    file2_id = File.objects.filter(name='data.csv').first().id

    assert Object.objects.count() == 2
    assert File.objects.count() == 2

    resp = client.get(f'/download/study/{study_id}/file/{file1_id}')
    assert resp.status_code == 200
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
    assert resp.content == b'aaa\nbbb\nccc\n'
    obj = Object.objects.first()
    assert obj.size == 12
    assert resp.get('Content-Length') == str(obj.size)

    resp = client.get(f'/download/study/{study_id}/file/{file2_id}')
    assert resp.content == b'aaa,bbb,ccc\nddd,eee,fff\n'


@mock_s3
def test_download_s3(client, db, tmp_uploads_s3):
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
    assert resp.status_code == 200
    study_id = studies[0].kf_id
    file_id = File.objects.first().id
    resp = client.get(f'/download/study/{study_id}/file/{file_id}')
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
    assert resp.content == b'aaa\nbbb\nccc\n'
    obj = Object.objects.first()
    assert obj.size == 12
    assert resp.get('Content-Length') == str(obj.size)


def test_no_file(client, db):
    resp = client.get(f'/download/study/study_id/file/123')
    assert resp.status_code == 404
