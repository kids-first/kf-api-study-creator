import os
import pytest
import json
import boto3
from moto import mock_s3

from django.conf import settings
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, Membership
from creator.files.models import Version, File

from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()


@mock_s3
def test_upload_query_s3(db, clients, upload_file, tmp_uploads_s3):
    s3 = boto3.client("s3")
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(2)
    study_id = studies[0].kf_id
    bucket = tmp_uploads_s3(studies[0].bucket)
    resp = upload_file(study_id, "manifest.txt", client)
    contents = s3.list_objects(Bucket=studies[0].bucket)["Contents"]
    assert len(contents) == 1
    assert contents[0]["Key"].endswith("manifest.txt")
    assert contents[0]["Key"].startswith(settings.UPLOAD_DIR)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    f = resp.json()["data"]["createFile"]["file"]
    assert f["fileType"] == "OTH"
    assert f["description"] == "This is my test file"
    assert f["name"] == "Test file"
    assert f["kfId"] == resp.json()["data"]["createFile"]["file"]["kfId"]
    assert f["tags"] == ["tag1", "tag2"]
    assert studies[0].files.count() == 1
    assert studies[-1].files.count() == 0


@mock_s3
def test_boto_fail(db, clients, upload_version, tmp_uploads_s3):
    """
    Test that the error response from a file mutation does not contain any
    boto errors from s3, only a predefined error message.
    """
    client = clients.get("Administrators")
    s3 = boto3.client("s3")
    study = StudyFactory()
    study_id = study.kf_id
    bucket = tmp_uploads_s3("not-correct-bucket")
    # Should fail because the study bucket was not created as expected
    resp = upload_version("manifest.txt", study_id=study_id, client=client)
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Failed to save file"

    # Check that no files or objects were created
    assert File.objects.count() == 0
    assert Version.objects.count() == 0


def test_upload_query_local(db, clients, tmp_uploads_local, upload_file):
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", client)
    user = User.objects.filter(groups__name="Administrators").first()
    obj = Version.objects.first()
    assert obj.creator == user
    assert len(tmp_uploads_local.listdir()) == 1
    assert (
        tmp_uploads_local.listdir()[0]
        .listdir()[0]
        .strpath.endswith("manifest.txt")
    )
    assert obj.key.path.startswith(
        os.path.join(
            settings.UPLOAD_DIR, obj.root_file.study.bucket, "manifest"
        )
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    f = resp.json()["data"]["createFile"]["file"]
    assert f["fileType"] == "OTH"
    assert f["description"] == "This is my test file"
    assert f["name"] == "Test file"
    assert f["kfId"] == resp.json()["data"]["createFile"]["file"]["kfId"]
    assert f["tags"] == ["tag1", "tag2"]
    assert studies[-1].files.count() == 1


def test_upload_version(
    db, clients, tmp_uploads_local, upload_file, upload_version
):
    """
    Test upload of intial file followed by a new version
    """
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(1)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", client)

    assert Study.objects.count() == 1
    assert File.objects.count() == 1
    assert Version.objects.count() == 1

    study = Study.objects.first()
    sf = File.objects.first()
    obj = Version.objects.first()
    user = User.objects.filter(groups__name="Administrators").first()
    assert obj.state == "PEN"
    assert obj.creator == user

    # Upload second version
    resp = upload_version("manifest.txt", file_id=sf.kf_id, client=client)

    # assert len(tmp_uploads_local.listdir()) == 2
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    version = resp.json()["data"]["createVersion"]["version"]
    assert "analysis" in version
    assert "id" in version
    assert "kfId" in version
    assert version["fileName"] == "manifest.txt"

    assert Study.objects.count() == 1
    assert File.objects.count() == 1
    assert Version.objects.count() == 2
    assert Version.objects.first().file_name == "manifest.txt"


def test_upload_version_no_file(
    db, clients, tmp_uploads_local, upload_file, upload_version
):
    """
    Tests that a new version may not be uploaded for a file that does not
    exist.
    """
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(1)
    study_id = studies[-1].kf_id

    # Upload a version with a file_id that does not exist
    resp = upload_version("manifest.txt", file_id="SF_XXXXXXXX", client=client)

    assert len(tmp_uploads_local.listdir()) == 0
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "File does not exist."

    assert Study.objects.count() == 1
    assert File.objects.count() == 0
    assert Version.objects.count() == 0


def test_study_not_exist(db, clients, upload_file):
    client = clients.get("Administrators")
    study_id = 10
    resp = upload_file(study_id, "manifest.txt", client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "Study matching query does not exist."
    assert resp.json()["errors"][0]["message"] == expected


def test_file_too_large(db, clients, upload_file, settings):
    client = clients.get("Administrators")
    settings.FILE_MAX_SIZE = 1
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, "manifest.txt", client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "File is too large."
    assert resp.json()["errors"][0]["message"] == expected


def test_upload_unauthed(db, upload_file):
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt")
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "Not allowed"
    assert resp.json()["errors"][0]["message"] == expected


def test_upload_unauthed_study(db, clients, upload_file):
    client = clients.get("Investigators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "manifest.txt", client)
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Not allowed"

    # Add investigator to study
    user = User.objects.filter(groups__name="Investigators").first()
    Membership(collaborator=user, study=study).save()

    resp = upload_file(study.kf_id, "manifest.txt", client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    f = resp.json()["data"]["createFile"]["file"]
    assert f["fileType"] == "OTH"
    assert f["description"] == "This is my test file"
    assert f["name"] == "Test file"
    assert f["kfId"] == resp.json()["data"]["createFile"]["file"]["kfId"]
    assert f["tags"] == ["tag1", "tag2"]
    assert study.files.count() == 1


def test_required_file_fields(
    db, clients, tmp_uploads_local, upload_file, upload_version
):
    """
    Test that name, description, and fileType are required for new files
    """
    client = clients.get("Administrators")
    studies = StudyFactory.create_batch(1)
    study_id = to_global_id("StudyNode", studies[-1].kf_id)
    file_name = "manifest.txt"
    query = """
        mutation (
            $study: ID!
        ) {
            createFile(
              study: $study
            ) {
                file { name description fileType }
          }
        }
    """
    study = Study.objects.first()
    with open(f"tests/data/{file_name}") as f:
        data = {"query": query.strip(), "variables": {"study": study_id}}
        resp = client.post(
            "/graphql", content_type="application/json", data=data
        )

    for error in resp.json()["errors"]:
        assert (
            "name" in error["message"]
            or "version" in error["message"]
            or "description" in error["message"]
            or "fileType" in error["message"]
        ) and "is required" in error["message"]


def test_creator(db, clients, tmp_uploads_local, upload_file, upload_version):
    """
    Test that creator is added to versions and files
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    study_id = study.kf_id
    resp = upload_file(study_id, "manifest.txt", client)

    sf = File.objects.first()
    obj = Version.objects.first()
    user = User.objects.filter(groups__name="Administrators").first()
    assert obj.creator == user

    query = """
    query ($kfId: String!) {
        fileByKfId(kfId: $kfId) {
            kfId
            creator { username }
            versions { edges { node { creator { username } } } }
        }
    }"""
    resp = client.post(
        "/graphql",
        data={"query": query, "variables": {"kfId": sf.kf_id}},
        content_type="application/json",
    )

    assert resp.json()["data"]["fileByKfId"] == {
        "kfId": sf.kf_id,
        "creator": {"username": "Administrators User"},
        "versions": {
            "edges": [
                {"node": {"creator": {"username": "Administrators User"}}}
            ]
        },
    }
