import os
import pytest
import json
import boto3
from moto import mock_s3

from creator.files.models import Object, File
from creator.studies.factories import StudyFactory


def test_download_local(client, db, tmp_uploads_local, upload_file):
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
def test_download_s3(client, db, tmp_uploads_s3, upload_file):
    s3 = boto3.client('s3')
    studies = StudyFactory.create_batch(2)
    bucket = tmp_uploads_s3(studies[0].bucket)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, 'manifest.txt')
    file_id = File.objects.first().id
    assert resp.status_code == 200
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


def test_download_field(client, db, upload_file):
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, 'manifest.txt')
    file_id = File.objects.filter(name='manifest.txt').first().id
    assert File.objects.count() == 1
    query = '''
        {
          allFiles {
            edges {
              node {
                downloadUrl
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
    file = resp.json()['data']['allFiles']['edges'][0]['node']
    expect_url = f'http://testserver/download/study/{study_id}/file/{file_id}'
    assert resp.status_code == 200
    assert 'data' in resp.json()
    assert 'allFiles' in resp.json()['data']
    assert file['downloadUrl'] == expect_url
    resp = client.get(file['downloadUrl'])
    assert resp.status_code == 200
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
