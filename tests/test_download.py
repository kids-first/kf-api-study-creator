import os
import pytest
import json
import boto3
from moto import mock_s3

from creator.files.models import Object, File
from creator.studies.factories import StudyFactory


def test_download_local(admin_client, db, tmp_uploads_local, upload_file):
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp1 = upload_file(study_id, 'manifest.txt', admin_client)
    file1_id = File.objects.filter(name='manifest.txt').first().kf_id
    version1_id = (File.objects.filter(name='manifest.txt')
                       .first().versions.first().kf_id)
    resp2 = upload_file(study_id, 'data.csv', admin_client)
    file2_id = File.objects.filter(name='data.csv').first().kf_id
    version2_id = (File.objects.filter(name='data.csv')
                       .first().versions.first().kf_id)

    assert Object.objects.count() == 2
    assert File.objects.count() == 2
    resp = admin_client.get(f'/download/study/{study_id}/file/{file1_id}'
                            f'/version/{version1_id}')
    assert resp.status_code == 200
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
    assert resp.content == b'aaa\nbbb\nccc\n'
    obj = File.objects.get(kf_id=file1_id).versions.first()
    assert obj.size == 12
    assert resp.get('Content-Length') == str(obj.size)

    resp = admin_client.get(f'/download/study/{study_id}/file/{file2_id}'
                            f'/version/{version2_id}')
    assert resp.content == b'aaa,bbb,ccc\nddd,eee,fff\n'


@mock_s3
def test_download_s3(admin_client, db, tmp_uploads_s3, upload_file):
    s3 = boto3.client('s3')
    studies = StudyFactory.create_batch(2)
    bucket = tmp_uploads_s3(studies[0].bucket)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, 'manifest.txt', admin_client)
    file_id = File.objects.first().kf_id
    version_id = (File.objects.filter(name='manifest.txt')
                      .first().versions.first().kf_id)
    assert resp.status_code == 200
    resp = admin_client.get(f'/download/study/{study_id}/file/{file_id}'
                            f'/version/{version_id}')
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
    assert resp.content == b'aaa\nbbb\nccc\n'
    obj = Object.objects.first()
    assert obj.size == 12
    assert resp.get('Content-Length') == str(obj.size)


def test_no_file(admin_client, db):
    resp = admin_client.get(f'/download/study/study_id/file/123')
    assert resp.status_code == 404


def test_download_field(admin_client, db, upload_file):
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, 'manifest.txt', admin_client)
    file_id = File.objects.filter(name='manifest.txt').first().kf_id
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
    resp = admin_client.post(
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
    resp = admin_client.get(file['downloadUrl'])
    assert resp.status_code == 200
    assert (resp.get('Content-Disposition') ==
            'attachment; filename=manifest.txt')
