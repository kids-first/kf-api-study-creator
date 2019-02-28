import os
import shutil
import pytest
import boto3
import json
import jwt

from django.test.client import Client


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
    def upload(study_id, file_name, client=client):
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


@pytest.fixture
def token():
    def make_token(groups=None, roles=None):
        """
        Returns an ego JWT for a user with given roles and groups
        """
        if groups is None:
            groups = []
        if roles is None:
            roles = ['USER']

        token = {
          "iat": 1551293729,
          "exp": 1551380129,
          "sub": "cfa211bc-6fa8-4a03-bb81-cf377f99da47",
          "iss": "ego",
          "aud": [],
          "jti": "7b42a89d-85e3-4954-81a0-beccb12f32d5",
          "context": {
            "user": {
              "name": "user@d3b.center",
              "email": "user@d3b.center",
              "status": "Approved",
              "firstName": "Bobby",
              "lastName": "TABLES;",
              "createdAt": 1531440000000,
              "lastLogin": 1551293729279,
              "preferredLanguage": None,
              "groups": groups,
              "roles": roles,
              "permissions": []
            }
          }
        }

        return jwt.encode(token, 'secret', algorithm='HS256').decode('utf8')
    return make_token


@pytest.fixture()
def admin_client(token):
    """
    Returns a client that sends an admin token with every request
    """
    admin_token = token([], ['ADMIN'])
    client = Client(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    return client


@pytest.fixture()
def user_client(token):
    """
    Returns a client for a logged in user
    """
    user_token = token(['SD_00000000'], ['USER'])
    client = Client(HTTP_AUTHORIZATION=f'Bearer {user_token}')
    return client
