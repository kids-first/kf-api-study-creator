import pytest
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.files.models import File

from creator.files.factories import FileFactory

User = get_user_model()


def test_default_types(db, clients, upload_file):
    """
    Test that default types are always in the valid_types.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "manifest.txt", client)

    kf_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=kf_id)

    assert set(file.valid_types) == set(
        ["OTH", "SEQ", "SHM", "CLN", "DBG", "FAM"]
    )


def test_s3_scrape(db, clients, upload_file):
    """
    Test that s3 scrape type is included for valid files.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "SD_ME0WME0W/s3_scrape.csv", client)

    kf_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=kf_id)

    assert "S3S" in file.valid_types
