import pytest
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.models import Study
from creator.studies.factories import StudyFactory
from creator.files.models import File
from creator.analyses.file_types import FILE_TYPES

from creator.files.factories import FileFactory, VersionFactory

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
    version = file.versions.latest("created_at")

    assert set(file.valid_types) == {
        ft for ft, obj in FILE_TYPES.items() if not obj["template"]
    }
    assert file.valid_types == version.valid_types


def test_s3_scrape(db, clients, upload_file):
    """
    Test that s3 scrape type is included for valid files.
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "SD_ME0WME0W/s3_scrape.csv", client)

    kf_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=kf_id)
    version = file.versions.latest("created_at")

    assert "S3S" in file.valid_types
    assert file.valid_types == version.valid_types


def test_set_storage(db, settings):
    """
    Test Version.set_storage
    """
    # File storage
    fv = VersionFactory()
    fv.set_storage()
    assert "FileSystemStorage" in str(fv.key.storage)

    # S3 storage - get study from root_file
    s3_storage = "django_s3_storage.storage.S3Storage"
    settings.DEFAULT_FILE_STORAGE = s3_storage
    fv.set_storage()
    assert fv.key.storage.settings.AWS_S3_BUCKET_NAME == (
        fv.root_file.study.bucket
    )

    # S3 storage - get study from prop
    study = fv.root_file.study
    fv.study = study
    fv.set_storage()
    assert fv.key.storage.settings.AWS_S3_BUCKET_NAME == (
        fv.root_file.study.bucket
    )

    # No study
    fv.root_file = None
    fv.study = None
    with pytest.raises(Study.DoesNotExist):
        fv.set_storage()
