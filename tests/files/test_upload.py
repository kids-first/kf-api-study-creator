import os
import pytest
import json
import boto3
from moto import mock_s3

from django.conf import settings

from creator.studies.factories import StudyFactory
from creator.studies.models import Study
from creator.files.models import Version, File


@mock_s3
def test_upload_query_s3(admin_client, db, upload_file, tmp_uploads_s3):
    s3 = boto3.client("s3")
    studies = StudyFactory.create_batch(2)
    study_id = studies[0].kf_id
    bucket = tmp_uploads_s3(studies[0].bucket)
    resp = upload_file(study_id, "manifest.txt", admin_client)
    contents = s3.list_objects(Bucket=studies[0].bucket)["Contents"]
    assert len(contents) == 1
    assert contents[0]["Key"].endswith("manifest.txt")
    assert contents[0]["Key"].startswith(settings.UPLOAD_DIR)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    assert resp.json() == {
        "data": {
            "createFile": {"success": True, "file": {"name": "manifest"}}
        }
    }
    assert studies[0].files.count() == 1
    assert studies[-1].files.count() == 0


@mock_s3
def test_boto_fail(admin_client, db, upload_file, tmp_uploads_s3):
    """
    Test that the error response from a file mutation does not contain any
    boto errors from s3, only a predefined error message.
    """
    s3 = boto3.client("s3")
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    bucket = tmp_uploads_s3("not-correct-bucket")
    # Should fail because the study bucket was not created as expected
    resp = upload_file(study_id, "manifest.txt", admin_client)
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "Failed to save file"

    # Check that no files or objects were created
    assert File.objects.count() == 0
    assert Version.objects.count() == 0


def test_upload_query_local(admin_client, db, tmp_uploads_local, upload_file):
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    obj = Version.objects.first()
    assert len(tmp_uploads_local.listdir()) == 1
    assert (
        tmp_uploads_local.listdir()[0]
        .listdir()[0]
        .strpath.endswith("manifest.txt")
    )
    assert obj.key.path.startswith(
        os.path.join(
            settings.UPLOAD_DIR, obj.root_file.study.bucket, "manifest.txt"
        )
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    assert resp.json() == {
        "data": {
            "createFile": {"success": True, "file": {"name": "manifest"}}
        }
    }
    assert studies[-1].files.count() == 1


def test_upload_version(
    admin_client, db, tmp_uploads_local, upload_file, upload_version
):
    """
    Test upload of intial file followed by a new version
    """
    studies = StudyFactory.create_batch(1)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)

    assert Study.objects.count() == 1
    assert File.objects.count() == 1
    assert Version.objects.count() == 1

    study = Study.objects.first()
    sf = File.objects.first()
    obj = Version.objects.first()
    assert obj.state == "PEN"

    # Upload second version
    resp = upload_version(
        study_id, "manifest.txt", admin_client, file_id=sf.kf_id
    )

    # assert len(tmp_uploads_local.listdir()) == 2
    print(resp.json())
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    assert resp.json()["data"]["createFile"] == {
        "success": True,
        "file": {
            "name": "manifest",
            "versions": {
                "edges": [
                    {"node": {"fileName": "manifest.txt"}},
                    {"node": {"fileName": "manifest.txt"}},
                ]
            },
        },
    }

    assert Study.objects.count() == 1
    assert File.objects.count() == 1
    assert Version.objects.count() == 2
    assert Version.objects.first().file_name == "manifest.txt"


def test_upload_version_no_file(
    admin_client, db, tmp_uploads_local, upload_file, upload_version
):
    """
    Tests that a new version may not be uploaded for a file that does not
    exist.
    """
    studies = StudyFactory.create_batch(1)
    study_id = studies[-1].kf_id

    # Upload a version with a file_id that does not exist
    resp = upload_version(
        study_id, "manifest.txt", admin_client, file_id="SF_XXXXXXXX"
    )

    assert len(tmp_uploads_local.listdir()) == 0
    assert resp.status_code == 200
    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == "File does not exist."

    assert Study.objects.count() == 1
    assert File.objects.count() == 0
    assert Version.objects.count() == 0


def test_study_not_exist(admin_client, db, upload_file):
    study_id = 10
    resp = upload_file(study_id, "manifest.txt", admin_client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "Study matching query does not exist."
    assert resp.json()["errors"][0]["message"] == expected


def test_file_too_large(admin_client, db, upload_file, settings):
    settings.FILE_MAX_SIZE = 1
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "File is too large."
    assert resp.json()["errors"][0]["message"] == expected


def test_upload_unauthed(client, db, upload_file):
    studies = StudyFactory.create_batch(2)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt")
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "Not authenticated to upload a file."
    assert resp.json()["errors"][0]["message"] == expected


def test_upload_unauthed_study(user_client, db, upload_file):
    studies = StudyFactory.create_batch(1)
    study_id = studies[0].kf_id
    resp = upload_file(study_id, "manifest.txt", user_client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" in resp.json()
    expected = "Not authenticated to upload to the study."
    assert resp.json()["errors"][0]["message"] == expected

    my_study = Study(kf_id="SD_00000000", external_id="Test")
    my_study.save()
    resp = upload_file("SD_00000000", "manifest.txt", user_client)
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "errors" not in resp.json()
    assert resp.json() == {
        "data": {
            "createFile": {"success": True, "file": {"name": "manifest"}}
        }
    }
    assert my_study.files.count() == 1
