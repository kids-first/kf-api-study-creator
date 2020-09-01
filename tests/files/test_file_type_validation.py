import pytest
from django.contrib.auth import get_user_model
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.studies.models import Study, Membership
from creator.files.models import Version

from creator.studies.factories import StudyFactory
from creator.files.factories import FileFactory

User = get_user_model()


CREATE_FILE = """
    mutation (
        $version: ID!,
        $name: String!,
        $description: String!,
        $fileType: FileFileType!,
        $study: ID
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
                versions(orderBy: "-created_at") {
                    edges {
                        node {
                            id
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


def test_missing_columns(db, clients, upload_version):
    """
    Test that an error outlining missing columns is returned correctly
    """
    client = clients.get("Administrators")
    study = StudyFactory(kf_id="SD_ME0WME0W")

    resp = upload_version(
        "SD_ME0WME0W/FV_4DP2P2Y2_clinical.csv",
        study_id=study.kf_id,
        client=client,
    )
    version = resp.json()["data"]["createVersion"]["version"]["id"]

    variables = {
        "version": version,
        "name": "Test file",
        "study": to_global_id("StudyNode", study.kf_id),
        "description": "This is my test file",
        "fileType": "S3S",
        "tags": [],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "missing columns" in resp.json()["errors"][0]["message"]
    assert "ETag" in resp.json()["errors"][0]["message"]
    assert "Key" in resp.json()["errors"][0]["message"]


def test_partially_missing_columns(db, clients, upload_version):
    """
    Test that an error outlining missing columns is returned correctly
    """
    client = clients.get("Administrators")
    study = StudyFactory(kf_id="SD_ME0WME0W")

    resp = upload_version(
        "SD_ME0WME0W/s3_scrape_partial.csv",
        study_id=study.kf_id,
        client=client,
    )
    version = resp.json()["data"]["createVersion"]["version"]["id"]

    variables = {
        "version": version,
        "name": "Test file",
        "study": to_global_id("StudyNode", study.kf_id),
        "description": "This is my test file",
        "fileType": "S3S",
        "tags": [],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" in resp.json()
    assert "missing columns" in resp.json()["errors"][0]["message"]
    assert "ETag" in resp.json()["errors"][0]["message"]
    assert "Size" in resp.json()["errors"][0]["message"]
    assert "Bucket" not in resp.json()["errors"][0]["message"]
    assert "Key" not in resp.json()["errors"][0]["message"]


def test_extra_columns(db, clients, upload_version):
    """
    Test that an error outlining missing columns is returned correctly
    """
    client = clients.get("Administrators")
    study = StudyFactory(kf_id="SD_ME0WME0W")

    resp = upload_version(
        "SD_ME0WME0W/s3_scrape_extra.csv", study_id=study.kf_id, client=client
    )
    version = resp.json()["data"]["createVersion"]["version"]["id"]

    variables = {
        "version": version,
        "name": "Test file",
        "study": to_global_id("StudyNode", study.kf_id),
        "description": "This is my test file",
        "fileType": "S3S",
        "tags": [],
    }

    data = {"query": CREATE_FILE, "variables": variables}
    resp = client.post("/graphql", content_type="application/json", data=data)

    assert "errors" not in resp.json()
