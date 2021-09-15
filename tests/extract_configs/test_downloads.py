import os
import pytest
from django.http.response import HttpResponse
from django.conf import settings

from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory
from creator.analyses.file_types import FILE_TYPES


@pytest.mark.parametrize(
    "file_type",
    [
        file_type
        for file_type, params in FILE_TYPES.items()
        if not params["required_columns"]
    ],
)
def test_no_extract_configs(clients, db, mocker, file_type):
    """
    Test that user cannot download extract config for non-expedited file types
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    file.file_type = file_type
    file.save()
    resp = client.get(f"/extract_config/study/{study.kf_id}/file/{file.kf_id}")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "file_type,content",
    [
        ("FCM", "Complex Family"),
        ("FTR", "Family Trio"),
        ("PDA", "Participant Details"),
        ("PTD", "Participant Diseases"),
        ("PTP", "Participant Phenotypes"),
        ("GOB", "General Observations"),
        ("BCM", "Biospecimen Collection Manifest"),
        ("BBM", "Biobank Manifest"),
        ("ALM", "Aliquot Manifest"),
        ("S3S", "S3 Scrape"),
        ("GWO", "Genomic Workflow Output Manifest"),
    ],
)
def test_has_extract_config(clients, db, mocker, file_type, content):
    """
    Test that user can download extract config for expedited file types
    """
    extract_config_dir = os.path.join(
        settings.BASE_DIR, "extract_configs", "templates"
    )
    mock_resp = mocker.patch("creator.files.views.HttpResponse")
    mock_resp.return_value = HttpResponse(
        open(f"{extract_config_dir}/{FILE_TYPES[file_type]['template']}")
    )
    client = clients.get("Administrators")
    study = StudyFactory()
    file = FileFactory(study=study)
    file.file_type = file_type
    file.save()
    version = file.versions.latest("created_at")
    resp = client.get(f"/extract_config/study/{study.kf_id}/file/{file.kf_id}")
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''" f"{version.kf_id}_config.py"
    )
    assert b"/download/study/" in resp.content
    assert bytes(content, "utf-8") in resp.content


def test_file_not_exist(clients, db):
    client = clients.get("Administrators")
    resp = client.get("/extract_config/study/study_id/file/123")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_config_auth(db, mocker, clients, user_group, allowed):
    """
    For a given user_type attempting to extract config for a file in an
    authorized study, we expect them to be allowed/not allowed to download
    the config file.
    """
    client = clients.get(user_group)
    study = StudyFactory()
    file = FileFactory(study=study)
    file.file_type = "S3S"
    file.save()
    version = file.versions.latest("created_at")
    version.key = open("tests/data/manifest.txt")
    mock_resp = mocker.patch("creator.files.views._resolve_version")
    mock_resp.return_value = (file, version)

    expected_name = f"attachment; filename*=UTF-8''{version.kf_id}_config.py"
    resp = client.get(f"/extract_config/study/{study.kf_id}/file/{file.kf_id}")

    if allowed:
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == expected_name
        assert b"/download/study/" in resp.content
    else:
        assert resp.status_code == 401
        assert resp.content == b"Not authorized to extract config for the file"
        assert resp.get("Content-Disposition") is None
