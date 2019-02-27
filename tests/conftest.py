import os
import shutil
import pytest
import boto3
import json


@pytest.yield_fixture
def tmp_uploads_local(tmpdir, settings):
    settings.UPLOAD_DIR = os.path.join('./test_uploads', tmpdir)
    settings.DEFAULT_FILE_STORAGE = (
        'django.core.files.storage.FileSystemStorage'
    )
    yield tmpdir
    shutil.rmtree(str(tmpdir))


@pytest.yield_fixture
def tmp_uploads_s3(tmpdir, settings):
    settings.DEFAULT_FILE_STORAGE = (
        'django_s3_storage.storage.S3Storage'
    )

    def mock(bucket_name='kf-study-us-east-1-my-study'):
        client = boto3.client('s3')
        return client.create_bucket(Bucket=bucket_name)

    return mock


@pytest.yield_fixture
def upload_file(client):
    def upload(study_id, file_name):
        query = '''
            mutation ($file: Upload!, $studyId: String!) {
              createFile(file: $file, studyId: $studyId) {
                success
                file { name }
              }
            }
        '''
        with open(f'tests/data/{file_name}') as f:
            data = {
                'operations': json.dumps({
                    'query': query.strip(),
                    'variables': {
                        'file': None,
                        'studyId': study_id
                    },
                }),
                'file': f,
                'map': json.dumps({
                    'file': ['variables.file'],
                }),
            }
            resp = client.post('/graphql', data=data)
        return resp
    return upload
