import os
import datetime
import shutil
import pytest
import boto3
import json
import jwt
from unittest import mock

from django.test.client import Client
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.users.factories import UserFactory
from creator.files.models import File
from creator.files.factories import FileFactory
from creator.studies.factories import StudyFactory
from creator.studies.models import Study
from creator.groups import GROUPS


from tests.projects.fixtures import mock_cavatica_api

User = get_user_model()


@pytest.fixture(scope="module", autouse=True)
def auth0_key_mock():
    """
    Mocks out the response from the /.well-known/jwks.json endpoint on auth0
    """
    middleware = "creator.middleware.Auth0AuthenticationMiddleware"
    with mock.patch(f"{middleware}._get_new_key") as get_key:
        with open("tests/keys/jwks.json", "r") as f:
            get_key.return_value = json.load(f)["keys"][0]
            yield get_key


@pytest.fixture(scope="module", autouse=True)
def auth0_profile_mock():
    """
    Mocks out the Auth0 profile response from /userinfo
    """
    middleware = "creator.middleware.Auth0AuthenticationMiddleware"
    with mock.patch(f"{middleware}._get_profile") as get_prof:
        profile = {
            "sub": "google-oauth2|999999999999999999999",
            "given_name": "Bobby",
            "family_name": "Tables",
            "nickname": "bobby",
            "name": "Bobby Tables",
            "locale": "en",
            "updated_at": "2019-05-30T00:08:58.807Z",
            "email": "bobbytables@example.com",
            "email_verified": True,
            "https://kidsfirstdrc.org/permissions": [
                "read:files",
                "write:files",
            ],
            "https://kidsfirstdrc.org/groups": ["SD_ME0WME0W"],
            "https://kidsfirstdrc.org/roles": ["ADMIN"],
        }
        get_prof.return_value = profile
        yield get_prof


@pytest.fixture(scope="module", autouse=True)
def groups(django_db_setup, django_db_blocker):
    """
    Setup the default permission groups
    """
    with django_db_blocker.unblock():
        for group_name, permissions in GROUPS.items():
            g, created = Group.objects.get_or_create(
                name=group_name, defaults={"name": group_name}
            )

            for code in permissions:
                p = Permission.objects.get(codename=code)
                g.permissions.add(p)
            g.save()


@pytest.yield_fixture(scope="module", autouse=False)
def clients(django_db_setup, django_db_blocker, groups, token):
    """
    Sets up api test clients with a user for each permission group
    available.
    """
    clients = {}
    with django_db_blocker.unblock():
        for group in Group.objects.all():
            user = UserFactory(username=f"{group.name} User")
            user.groups.add(group)
            user_token = token([], [], sub=user.sub)
            client = Client(HTTP_AUTHORIZATION=f"Bearer {user_token}")
            clients[group.name] = client
        clients[None] = Client()
        yield clients

        # Remove groups and users to maintain state for next module
        Group.objects.all().delete()
        User.objects.all().delete()


@pytest.yield_fixture
def tmp_uploads_local(tmpdir, settings):
    settings.UPLOAD_DIR = os.path.join("./test_uploads", tmpdir)
    settings.DEFAULT_FILE_STORAGE = (
        "django.core.files.storage.FileSystemStorage"
    )
    yield tmpdir
    shutil.rmtree(str(tmpdir))


@pytest.yield_fixture
def tmp_uploads_s3(tmpdir, settings):
    settings.UPLOAD_DIR = "s3"
    settings.DEFAULT_FILE_STORAGE = "django_s3_storage.storage.S3Storage"

    def mock(bucket_name="kf-study-us-east-1-my-study"):
        client = boto3.client("s3")
        return client.create_bucket(Bucket=bucket_name)

    return mock


@pytest.yield_fixture
def upload_file(client, tmp_uploads_local, upload_version):
    def upload(study_id, file_name, client=client):
        resp = upload_version(file_name, study_id=study_id, client=client)
        # If the upload fails, return the resulting errors instead of trying
        # to create a document
        if "errors" in resp.json():
            return resp
        version_id = resp.json()["data"]["createVersion"]["version"]["id"]
        query = """
            mutation (
                $version: ID!,
                $name: String!,
                $description: String!,
                $fileType: FileType!,
                $study: ID!
                $tags: [String]
            ) {
                createFile(
                  version: $version,
                  name: $name,
                  study: $study,
                  description: $description,
                  fileType: $fileType
                  tags: $tags
                ) {
                    file {
                        id
                        kfId
                        name
                        description
                        fileType
                        tags
                        validTypes
                        versions(orderBy: "-created_at") {
                            edges {
                                node {
                                    id
                                    kfId
                                    analysis {
                                        id
                                    }
                                }
                            }
                        }
                    }
              }
            }
        """
        with open(f"tests/data/{file_name}", "rb") as f:
            data = {
                "query": query.strip(),
                "variables": {
                    "version": version_id,
                    "name": "Test file",
                    "study": to_global_id("StudyNode", study_id),
                    "description": "This is my test file",
                    "fileType": "OTH",
                    "tags": ["tag1", "tag2"],
                },
            }
            resp = client.post(
                "/graphql", content_type="application/json", data=data
            )
        return resp

    return upload


@pytest.yield_fixture
def upload_version(client, tmp_uploads_local):
    """
    Uploads a new version of an existing file
    """

    def upload(file_name, study_id=None, file_id=None, client=client):
        query = """
            mutation (
                $file: Upload!,
                $description: String!,
                $fileId: String
                $study: ID
            ) {
                createVersion(
                file: $file,
                description: $description,
                fileId: $fileId
                study: $study
            ) {
                success
                version {
                    id
                    kfId
                    fileName
                    analysis {
                        id
                        knownFormat
                        nrows
                        ncols
                        columns
                    }
                }
              }
            }
        """
        with open(f"tests/data/{file_name}", "rb") as f:
            variables = {"file": None, "description": "my new version"}
            if file_id is not None:
                variables["fileId"] = file_id
            if study_id is not None:
                variables["study"] = to_global_id("StudyNode", study_id)
            data = {
                "operations": json.dumps(
                    {"query": query.strip(), "variables": variables}
                ),
                "file": f,
                "map": json.dumps({"file": ["variables.file"]}),
            }
            resp = client.post("/graphql", data=data)
        return resp

    return upload


@pytest.fixture(scope="module")
def token():
    """
    Returns a function that will generate a token for a user in given groups
    with given roles.
    """
    with open("tests/keys/private_key.pem", "rb") as f:
        key = f.read()

    def make_token(
        groups=None,
        roles=None,
        sub="cfa211bc-6fa8-4a03-bb81-cf377f99da47",
        exp=None,
    ):
        """
        Returns an Auth0 JWT for a user with given roles and groups.
        """
        if groups is None:
            groups = []
        if roles is None:
            roles = ["USER"]

        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        token = {
            "iat": now.timestamp(),
            "exp": exp if exp else tomorrow.timestamp(),
            "sub": sub,
            "iss": "Auth0",
            "aud": "creator",
            "jti": "7b42a89d-85e3-4954-81a0-beccb12f32d5",
        }

        token["https://kidsfirstdrc.org/groups"] = groups
        token["https://kidsfirstdrc.org/roles"] = roles
        token["aud"] = "https://kf-study-creator.kidsfirstdrc.org"

        return jwt.encode(token, key, algorithm="RS256").decode("utf8")

    return make_token


@pytest.fixture()
def service_token():
    """
    Generate a service token that will be used in machine-to-machine auth
    """
    with open("tests/keys/private_key.pem", "rb") as f:
        key = f.read()

    def make_token(scope="role:admin"):
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        token = {
            "iss": "auth0.com",
            "sub": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@clients",
            "aud": "https://kf-study-creator.kidsfirstdrc.org",
            "iat": now.timestamp(),
            "exp": tomorrow.timestamp(),
            "azp": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "scope": scope,
            "gty": "client-credentials",
        }
        return jwt.encode(token, key, algorithm="RS256").decode("utf8")

    return make_token


@pytest.fixture()
def admin_client(token):
    """
    Returns a client that sends an admin token with every request
    """
    admin_token = token([], ["ADMIN"])
    client = Client(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    return client


@pytest.fixture()
def service_client(service_token):
    """
    Returns a client that sends a service token with every request
    """
    token = service_token()
    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture()
def user_client(token):
    """
    Returns a client for a logged in user
    """
    user_token = token(["SD_00000000"], ["USER"])
    client = Client(HTTP_AUTHORIZATION=f"Bearer {user_token}")
    return client


@pytest.fixture
def prep_file(admin_client, upload_file):
    """
    1. Create one study
        authed = Ture -- study with ID 'SD_00000000' (available to user_client)
        authed = False -- study with random ID
    2. Upload one file to the study (default:manifest.txt)
    3. Return study_id, file_id, version_id
    """

    def file(file_name="manifest.txt", client=admin_client, authed=False):
        if authed:
            study_id = "SD_00000000"
            study = Study(kf_id=study_id, external_id="Test")
            study.save()
        else:
            studies = StudyFactory.create_batch(1)
            study_id = studies[0].kf_id

        upload = upload_file(study_id, file_name, client)
        study = Study.objects.get(kf_id=study_id)
        file_id = upload.json()["data"]["createFile"]["file"]["kfId"]
        version_id = File.objects.get(kf_id=file_id).versions.first().kf_id
        resp = (study_id, file_id, version_id)
        return resp

    return file


@pytest.fixture
def versions(db, clients, mocker):
    """
    Setup a file in a study with a new version that returns a mocked data file.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    version = file.versions.latest("created_at")
    version.key = open(f"tests/data/manifest.txt")

    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    return study, file, version
